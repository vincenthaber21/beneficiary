import io
import json
import re
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.utils.safestring import mark_safe
from datetime import timedelta
from utils import staff_required
from checker.logic import evaluate, VALID_CLASSES, INCOME_THRESHOLD
from records.models import GrantRecord
from .models import Beneficiary, FamilyMember
from .forms import BeneficiaryForm, FamilyMemberFormSet
from .household import household_cooldown, family_block_for


def _get_family_groups(beneficiaries):
    """Return beneficiaries grouped into family units via FamilyMember links.
    Each group is a dict: {label, members, is_family}.
    Multi-member groups are sorted first."""
    pk_to_ben = {b.pk: b for b in beneficiaries}
    ben_pks = set(pk_to_ben)

    adj = {pk: set() for pk in ben_pks}
    for ben_id, mem_id in (
        FamilyMember.objects
        .filter(beneficiary_id__in=ben_pks, member_id__in=ben_pks)
        .exclude(member__isnull=True)
        .values_list("beneficiary_id", "member_id")
    ):
        adj[ben_id].add(mem_id)
        adj[mem_id].add(ben_id)

    visited = set()
    raw_groups = []
    for b in beneficiaries:          # preserves original ordering
        if b.pk in visited:
            continue
        component = []
        stack = [b.pk]
        while stack:
            cur = stack.pop()
            if cur in visited:
                continue
            visited.add(cur)
            component.append(pk_to_ben[cur])
            stack.extend(adj[cur] - visited)
        raw_groups.append(component)

    # Multi-member families first, then individuals; each tier sorted by last name
    raw_groups.sort(key=lambda g: (len(g) == 1, g[0].last_name, g[0].first_name))

    result = []
    for group in raw_groups:
        last_names = sorted({b.last_name for b in group})
        label = " & ".join(last_names[:2])
        if len(last_names) > 2:
            label += f" +{len(last_names) - 2}"
        result.append({"label": label, "members": group, "is_family": len(group) > 1})
    return result


def _attach_eligibility(queryset):
    """Attach an ``eligibility_result`` dict to each Beneficiary in the queryset
    using a single extra query to find recent grants (avoids N+1). Also enforces
    the household rule: a grant to any family member blocks the whole family."""
    cutoff = timezone.now().date() - timedelta(days=90)
    recent_ids = set(
        GrantRecord.objects.filter(
            status="released", date_granted__gte=cutoff
        ).values_list("beneficiary_id", flat=True)
    )
    blocker_id_map, name_map, _ = household_cooldown(3)
    result_list = []
    for b in queryset:
        # Check both system grant records AND manually entered prior_grant_date
        has_recent = (
            b.pk in recent_ids
            or (b.prior_grant_date is not None and b.prior_grant_date >= cutoff)
        )
        family_blocker = None if has_recent else family_block_for(b.pk, blocker_id_map, name_map)
        b.family_blocker = family_blocker
        b.eligibility_result = evaluate(
            beneficiary_class=b.beneficiary_class,
            received_grant_within_3_months=has_recent,
            monthly_income=float(b.monthly_income),
            household_blocker_name=family_blocker,
        )
        result_list.append(b)
    return result_list


@staff_required
def beneficiary_list(request):
    q = request.GET.get("q", "").strip()
    cls = request.GET.get("class", "")
    fam = request.GET.get("family", "")
    claim = request.GET.get("claim", "").strip()
    qs = Beneficiary.objects.all()
    if q:
        qs = qs.filter(
            Q(last_name__icontains=q) | Q(first_name__icontains=q) |
            Q(rfid_id__icontains=q) | Q(contact_number__icontains=q)
        )
    if cls:
        qs = qs.filter(beneficiary_class=cls)

    claimed_ids = set(
        GrantRecord.objects.filter(status="released")
        .values_list("beneficiary_id", flat=True)
        .distinct()
    )
    if claim == "claimed":
        qs = qs.filter(pk__in=claimed_ids)
    elif claim == "not_claimed":
        qs = qs.exclude(pk__in=claimed_ids)

    # Beneficiaries that participate in at least one family link (either direction)
    linked_ids = set()
    for a, b in (
        FamilyMember.objects.exclude(member__isnull=True)
        .values_list("beneficiary_id", "member_id")
    ):
        linked_ids.add(a)
        linked_ids.add(b)
    if fam == "family":
        qs = qs.filter(pk__in=linked_ids)
    elif fam == "individual":
        qs = qs.exclude(pk__in=linked_ids)

    beneficiaries = _attach_eligibility(qs)

    # Mark beneficiaries who have received at least one released grant from a program
    from django.db.models import Count
    received_map = dict(
        GrantRecord.objects.filter(status="released")
        .values_list("beneficiary_id")
        .annotate(n=Count("id"))
        .values_list("beneficiary_id", "n")
    )
    for b in beneficiaries:
        b.received_count = received_map.get(b.pk, 0)
        b.has_received = b.received_count > 0

    family_groups = _get_family_groups(beneficiaries)
    family_count = sum(1 for g in family_groups if g["is_family"])
    received_count = sum(1 for b in beneficiaries if b.has_received)
    not_claimed_count = sum(1 for b in beneficiaries if not b.has_received)
    return render(request, "beneficiaries/list.html", {
        "beneficiaries": beneficiaries,
        "family_groups": family_groups,
        "total": len(beneficiaries),
        "family_count": family_count,
        "claimed_count": received_count,
        "not_claimed_count": not_claimed_count,
        "q": q, "cls": cls, "fam": fam, "claim": claim,
        "classes": VALID_CLASSES,
    })


@staff_required
def beneficiary_create(request):
    form = BeneficiaryForm(request.POST or None)
    formset = FamilyMemberFormSet(request.POST or None)
    for f in formset.forms:
        f.fields["member"].queryset = Beneficiary.objects.order_by("last_name", "first_name")
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        ben = form.save()
        formset.instance = ben
        formset.save()
        # Auto-validate: new beneficiary has no system grant records yet;
        # received_grant_within_months already checks prior_grant_date field.
        personal_recent = ben.received_grant_within_months(3)
        blocker_id_map, name_map, _ = household_cooldown(3)
        family_blocker = None if personal_recent else family_block_for(ben.pk, blocker_id_map, name_map)
        result = evaluate(
            beneficiary_class=ben.beneficiary_class,
            received_grant_within_3_months=personal_recent,
            monthly_income=float(ben.monthly_income),
            household_blocker_name=family_blocker,
        )
        if result["qualified"]:
            messages.success(request, f"Beneficiary added. Eligibility: QUALIFIED — {result['reason']}")
        else:
            messages.warning(request, f"Beneficiary added. Eligibility: NOT QUALIFIED — {result['reason']}")
        return redirect("beneficiaries:detail", pk=ben.pk)
    return render(request, "beneficiaries/form.html", {
        "form": form, "formset": formset, "action": "Add",
        "valid_classes_json": json.dumps(VALID_CLASSES),
        "income_threshold": INCOME_THRESHOLD,
    })


@staff_required
def beneficiary_update(request, pk):
    ben = get_object_or_404(Beneficiary, pk=pk)
    form = BeneficiaryForm(request.POST or None, instance=ben)
    formset = FamilyMemberFormSet(request.POST or None, instance=ben)
    for f in formset.forms:
        f.fields["member"].queryset = Beneficiary.objects.exclude(pk=pk).order_by("last_name", "first_name")
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        ben = form.save()
        formset.save()
        personal_recent = ben.received_grant_within_months(3)
        blocker_id_map, name_map, _ = household_cooldown(3)
        family_blocker = None if personal_recent else family_block_for(ben.pk, blocker_id_map, name_map)
        result = evaluate(
            beneficiary_class=ben.beneficiary_class,
            received_grant_within_3_months=personal_recent,
            monthly_income=float(ben.monthly_income),
            household_blocker_name=family_blocker,
        )
        if result["qualified"]:
            messages.success(request, f"Beneficiary updated. Eligibility: QUALIFIED — {result['reason']}")
        else:
            messages.warning(request, f"Beneficiary updated. Eligibility: NOT QUALIFIED — {result['reason']}")
        return redirect("beneficiaries:detail", pk=pk)
    # Most recent RELEASED grant on file (system record) — the edit page's live
    # preview must account for this, not just the manual prior_grant_date field.
    last_system_grant = (
        ben.grants.filter(status="released")
        .order_by("-date_granted")
        .values_list("date_granted", flat=True)
        .first()
    )

    # Household rule – a grant to any family member blocks the whole family.
    # Only relevant when this person hasn't personally received one recently.
    personal_recent = ben.received_grant_within_months(3)
    blocker_id_map, name_map, _ = household_cooldown(3)
    family_blocker = None if personal_recent else family_block_for(ben.pk, blocker_id_map, name_map)

    # Family connections in BOTH directions:
    #  • forward  → people listed as this person's family members
    #  • reverse  → other beneficiaries who list this person as their family member
    family_connections = []
    seen_person_ids = set()
    for fm in ben.family_members.filter(member__isnull=False).select_related("member"):
        family_connections.append({"person": fm.member, "relationship": fm.relationship, "age": fm.age})
        seen_person_ids.add(fm.member_id)
    for fm in ben.member_of.filter(member__isnull=False).select_related("beneficiary"):
        if fm.beneficiary_id in seen_person_ids:
            continue
        family_connections.append({"person": fm.beneficiary, "relationship": fm.relationship, "age": fm.age})
        seen_person_ids.add(fm.beneficiary_id)
    return render(request, "beneficiaries/form.html", {
        "form": form, "formset": formset, "action": "Edit", "beneficiary": ben,
        "existing_family_members": family_connections,
        "last_system_grant": last_system_grant.isoformat() if last_system_grant else "",
        "family_blocker": family_blocker or "",
        "valid_classes_json": json.dumps(VALID_CLASSES),
        "income_threshold": INCOME_THRESHOLD,
    })


@staff_required
def beneficiary_delete(request, pk):
    ben = get_object_or_404(Beneficiary, pk=pk)
    if request.method == "POST":
        ben.delete()
        messages.success(request, "Beneficiary removed.")
        return redirect("beneficiaries:list")
    return render(request, "beneficiaries/confirm_delete.html", {"beneficiary": ben})


@staff_required
def beneficiary_detail(request, pk):
    ben = get_object_or_404(Beneficiary, pk=pk)
    grants = ben.grants.select_related("program", "granted_by").order_by("-date_granted")

    cutoff = timezone.now().date() - timedelta(days=90)

    # Step 1 – class check
    valid_class = ben.beneficiary_class in VALID_CLASSES

    # Step 2 – grant cooldown check (system records + prior_grant_date)
    last_system_grant = (
        ben.grants.filter(status="released")
        .order_by("-date_granted")
        .values_list("date_granted", flat=True)
        .first()
    )
    system_grant_in_cooldown = last_system_grant is not None and last_system_grant >= cutoff
    prior_grant_in_cooldown = (
        ben.prior_grant_date is not None and ben.prior_grant_date >= cutoff
    )
    received_recent = system_grant_in_cooldown or prior_grant_in_cooldown

    # Determine the effective "most recent grant date" that is in cooldown
    cooldown_source_date = None
    if system_grant_in_cooldown and prior_grant_in_cooldown:
        cooldown_source_date = max(last_system_grant, ben.prior_grant_date)
    elif system_grant_in_cooldown:
        cooldown_source_date = last_system_grant
    elif prior_grant_in_cooldown:
        cooldown_source_date = ben.prior_grant_date
    cooldown_end = cooldown_source_date + timedelta(days=90) if cooldown_source_date else None

    # Step 3 – income check
    income_ok = float(ben.monthly_income) < INCOME_THRESHOLD

    # Household rule – a grant to any family member blocks the whole family
    blocker_id_map, name_map, _ = household_cooldown(3)
    family_blocker = None if received_recent else family_block_for(ben.pk, blocker_id_map, name_map)

    result = evaluate(
        beneficiary_class=ben.beneficiary_class,
        received_grant_within_3_months=received_recent,
        monthly_income=float(ben.monthly_income),
        household_blocker_name=family_blocker,
    )
    # Family connections (both directions)
    family_members = (
        ben.family_members
        .filter(member__isnull=False)
        .select_related("member")
        .order_by("relationship", "member__last_name")
    )
    also_in_families = (
        ben.member_of
        .filter(member__isnull=False)
        .select_related("beneficiary")
        .order_by("relationship", "beneficiary__last_name")
    )
    return render(request, "beneficiaries/detail.html", {
        "beneficiary": ben,
        "grants": grants,
        "result": result,
        "family_members": family_members,
        "also_in_families": also_in_families,
        # Decision-tree step context
        "valid_class": valid_class,
        "received_recent": received_recent,
        "system_grant_in_cooldown": system_grant_in_cooldown,
        "prior_grant_in_cooldown": prior_grant_in_cooldown,
        "cooldown_source_date": cooldown_source_date,
        "cooldown_end": cooldown_end,
        "family_blocker": family_blocker,
        "income_ok": income_ok,
        "income_threshold": INCOME_THRESHOLD,
    })


def _qr_svg(data):
    """Return an inline-embeddable SVG string for a QR code of ``data``.
    Uses qrcode's pure-Python SVG factory so no image library is required.
    The width/height are stripped so the card CSS controls sizing."""
    import qrcode
    import qrcode.image.svg as svg
    qr = qrcode.QRCode(box_size=10, border=1, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(image_factory=svg.SvgPathImage)
    buf = io.BytesIO()
    img.save(buf)
    out = buf.getvalue().decode()
    out = re.sub(r"<\?xml[^>]*\?>\s*", "", out)          # drop XML declaration
    out = re.sub(r'\swidth="[^"]*"', "", out, count=1)   # let CSS size it
    out = re.sub(r'\sheight="[^"]*"', "", out, count=1)
    return mark_safe(out)


@staff_required
def generate_id(request, pk):
    """Assign (or return the existing) e-Bahagi ID number for a beneficiary and
    return it as JSON, so the ID / Fingerprint Tap page can display it inline
    without navigating away. Format: EB-<year>-<zero-padded pk>."""
    from django.http import JsonResponse
    ben = get_object_or_404(Beneficiary, pk=pk)
    had_id = bool(ben.rfid_id)
    id_number = ben.ensure_id_number()
    return JsonResponse({"id_number": id_number, "newly_generated": not had_id})


def _build_card(ben):
    """Build the context dict for one printable e-Bahagi ID card. Auto-issues an
    ID number if one hasn't been assigned yet and embeds a scannable QR code."""
    id_number = ben.ensure_id_number()
    address_line = ", ".join(
        p for p in (ben.address, ben.barangay, ben.municipality) if p
    )
    return {
        "beneficiary": ben,
        "id_number": id_number,
        "address_line": address_line,
        "qr_svg": _qr_svg(id_number),
    }


@staff_required
def beneficiary_id_card(request, pk):
    """Render a printable e-Bahagi ID card for a single beneficiary."""
    ben = get_object_or_404(Beneficiary, pk=pk)
    return render(request, "beneficiaries/id_card.html", {"card": _build_card(ben)})


@staff_required
def beneficiary_id_cards_all(request):
    """Render printable e-Bahagi ID cards for every beneficiary, one per page."""
    cards = [
        _build_card(ben)
        for ben in Beneficiary.objects.order_by("last_name", "first_name")
    ]
    return render(request, "beneficiaries/id_cards_all.html", {"cards": cards})


@staff_required
def rfid_check(request):
    from citizens.fingerprint_match import find_best_fingerprint
    from citizens.models import CitizenFingerprint

    beneficiary = None
    result = None
    error = None
    rfid = ""
    if request.method == "POST":
        rfid = request.POST.get("rfid_id", "").strip()
        if rfid:
            try:
                beneficiary = Beneficiary.objects.get(rfid_id=rfid)
            except Beneficiary.DoesNotExist:
                # Exact fingerprint template / hash match first.
                fp = (
                    CitizenFingerprint.objects.select_related("citizen")
                    .filter(template_data=rfid)
                    .order_by("-is_primary", "-registered_at")
                    .first()
                )
                # Fuzzy aHash match (DS-K1F820-F live scans vary slightly).
                if not fp:
                    fp, _dist = find_best_fingerprint(rfid, threshold=10)

                if fp:
                    citizen = fp.citizen
                    beneficiary = Beneficiary.objects.filter(
                        last_name__iexact=citizen.last_name,
                        first_name__iexact=citizen.first_name,
                    ).first()
                    if not beneficiary and citizen.rfid_tag:
                        beneficiary = Beneficiary.objects.filter(
                            rfid_id=citizen.rfid_tag
                        ).first()
                    if not beneficiary:
                        error = (
                            f'Fingerprint matched citizen "{citizen.full_name}" '
                            f"({citizen.registry_no}), but no beneficiary record was found."
                        )
                else:
                    error = f'No beneficiary found with ID / fingerprint "{rfid}".'

            if beneficiary:
                personal_recent = beneficiary.received_grant_within_months(3)
                blocker_id_map, name_map, _ = household_cooldown(3)
                family_blocker = (
                    None if personal_recent
                    else family_block_for(beneficiary.pk, blocker_id_map, name_map)
                )
                result = evaluate(
                    beneficiary_class=beneficiary.beneficiary_class,
                    received_grant_within_3_months=personal_recent,
                    monthly_income=float(beneficiary.monthly_income),
                    household_blocker_name=family_blocker,
                )
        else:
            error = "Please enter or scan an ID / fingerprint."
    return render(request, "beneficiaries/rfid.html", {
        "beneficiary": beneficiary, "result": result, "error": error, "rfid": rfid,
    })
