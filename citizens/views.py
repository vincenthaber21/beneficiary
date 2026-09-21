from types import SimpleNamespace

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from beneficiaries.views import _qr_svg
from utils import staff_required

from django.urls import reverse

from .forms import CitizenForm, CitizenFamilyFormSet, make_citizen_fingerprint_formset
from .models import Citizen
from .search import search_citizens

_CREATE_INITIAL = {
    "municipality": "Bacnotan",
    "province": "La Union",
}


def _build_card(citizen):
    """Context dict for the shared e-Bahagi ID card template.
    Auto-issues a Citizen ID (registry_no) when opening a printable card,
    matching beneficiary Generate ID behaviour."""
    if citizen and citizen.pk:
        id_number = citizen.ensure_id_number()
        address_line = ", ".join(
            p for p in (citizen.address, citizen.barangay, citizen.municipality) if p
        )
        return {
            "beneficiary": citizen,
            "id_number": id_number,
            "address_line": address_line,
            "qr_svg": _qr_svg(id_number),
        }
    return {
        "beneficiary": SimpleNamespace(
            last_name="",
            first_name="",
            middle_name="",
            date_of_birth=None,
            signature="",
        ),
        "id_number": "—",
        "address_line": "",
        "qr_svg": None,
    }


def _build_form_card(citizen=None):
    """Live preview card for the add/edit form — never auto-issues an ID."""
    if citizen and citizen.pk:
        address_line = ", ".join(
            p for p in (citizen.address, citizen.barangay, citizen.municipality) if p
        )
        id_number = citizen.registry_no or "—"
        return {
            "beneficiary": citizen,
            "id_number": id_number,
            "address_line": address_line,
            "qr_svg": _qr_svg(id_number) if citizen.registry_no else None,
        }
    return _build_card(None)


def _save_citizen_with_related(form, family_formset, fingerprint_formset):
    with transaction.atomic():
        citizen = form.save()
        family_formset.instance = citizen
        family_formset.save()
        fingerprint_formset.instance = citizen
        fingerprint_formset.save()
    return citizen


@staff_required
def citizen_list(request):
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    barangay = request.GET.get("barangay", "").strip()
    aid = request.GET.get("aid", "").strip()  # enrolled | not_enrolled | availed | ""

    qs = Citizen.objects.select_related("beneficiary").all()
    if q:
        qs = qs.filter(
            Q(registry_no__icontains=q)
            | Q(last_name__icontains=q)
            | Q(first_name__icontains=q)
            | Q(middle_name__icontains=q)
            | Q(philsys_id__icontains=q)
            | Q(voter_id__icontains=q)
            | Q(contact_number__icontains=q)
            | Q(other_id_number__icontains=q)
            | Q(rfid_tag__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)
    if barangay:
        qs = qs.filter(barangay__iexact=barangay)
    if aid == "enrolled":
        qs = qs.filter(beneficiary__isnull=False)
    elif aid == "not_enrolled":
        qs = qs.filter(beneficiary__isnull=True)
    elif aid == "availed":
        # Enrolled and has at least one released grant, or a prior_grant_date on file.
        qs = qs.filter(beneficiary__isnull=False).filter(
            Q(beneficiary__grants__status="released")
            | Q(beneficiary__prior_grant_date__isnull=False)
        ).distinct()

    barangays = (
        Citizen.objects.exclude(barangay="")
        .values_list("barangay", flat=True)
        .distinct()
        .order_by("barangay")
    )

    enrolled_count = Citizen.objects.filter(beneficiary__isnull=False).count()
    total = qs.count()
    paginator = Paginator(qs, 50)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "citizens": page_obj.object_list,
        "page_obj": page_obj,
        "total": total,
        "q": q,
        "status": status,
        "barangay": barangay,
        "aid": aid,
        "barangays": barangays,
        "status_choices": Citizen.STATUS_CHOICES,
        "count_active": Citizen.objects.filter(status="active").count(),
        "count_inactive": Citizen.objects.exclude(status="active").count(),
        "count_enrolled": enrolled_count,
    }
    return render(request, "citizens/list.html", context)


@staff_required
def citizen_detail(request, pk):
    citizen = get_object_or_404(
        Citizen.objects.select_related("beneficiary").prefetch_related(
            "family_members__member", "fingerprints", "beneficiary__grants"
        ),
        pk=pk,
    )
    beneficiary = None
    try:
        beneficiary = citizen.beneficiary
    except ObjectDoesNotExist:
        beneficiary = None
    last_grant = None
    grant_count = 0
    if beneficiary is not None:
        released = beneficiary.grants.filter(status="released").order_by("-date_granted")
        grant_count = released.count()
        last = released.first()
        last_grant = last.date_granted if last else beneficiary.prior_grant_date
    return render(
        request,
        "citizens/detail.html",
        {
            "citizen": citizen,
            "card": _build_card(citizen),
            "beneficiary": beneficiary,
            "last_grant": last_grant,
            "grant_count": grant_count,
            "has_availed": bool(last_grant) or grant_count > 0,
        },
    )


def _family_form_context(citizen=None):
    return {
        "citizen_search_url": reverse("citizens:search"),
        "exclude_citizen_pk": citizen.pk if citizen and citizen.pk else "",
    }


@staff_required
def citizen_search(request):
    """JSON typeahead for linking family members (cached)."""
    q = request.GET.get("q", "").strip()
    exclude = request.GET.get("exclude", "").strip()
    exclude_pk = int(exclude) if exclude.isdigit() else None
    results = search_citizens(q, exclude_pk=exclude_pk)
    return JsonResponse({
        "ok": True,
        "query": q,
        "count": len(results),
        "results": results,
    })


@staff_required
def citizen_create(request):
    form = CitizenForm(request.POST or None, request.FILES or None, initial=_CREATE_INITIAL)
    formset = CitizenFamilyFormSet(request.POST or None, prefix="family")
    fingerprint_formset = make_citizen_fingerprint_formset(
        request.POST or None, prefix="fp"
    )
    next_url = (request.GET.get("next") or request.POST.get("next") or "").strip()
    if (
        request.method == "POST"
        and form.is_valid()
        and formset.is_valid()
        and fingerprint_formset.is_valid()
    ):
        try:
            citizen = _save_citizen_with_related(form, formset, fingerprint_formset)
        except IntegrityError:
            messages.error(
                request,
                "A fingerprint you scanned is already registered to another person. "
                "Each finger must be unique.",
            )
        else:
            messages.success(
                request,
                f'Citizen "{citizen.full_name}" registered ({citizen.registry_no}).',
            )
            # Return to beneficiary enroll flow when requested.
            if next_url.startswith("/beneficiaries/add"):
                sep = "&" if "?" in next_url else "?"
                return redirect(f"{next_url}{sep}citizen={citizen.pk}")
            if next_url.startswith("/"):
                return redirect(next_url)
            return redirect("citizens:detail", pk=citizen.pk)
    return render(
        request,
        "citizens/form.html",
        {
            "form": form,
            "formset": formset,
            "fingerprint_formset": fingerprint_formset,
            "action": "Add",
            "citizen": None,
            "card": _build_form_card(None),
            "next_url": next_url,
            **_family_form_context(None),
        },
    )


@staff_required
def citizen_update(request, pk):
    citizen = get_object_or_404(Citizen, pk=pk)
    form = CitizenForm(
        request.POST or None, request.FILES or None, instance=citizen
    )
    formset = CitizenFamilyFormSet(
        request.POST or None, instance=citizen, prefix="family"
    )
    fingerprint_formset = make_citizen_fingerprint_formset(
        request.POST or None, instance=citizen, prefix="fp"
    )
    if (
        request.method == "POST"
        and form.is_valid()
        and formset.is_valid()
        and fingerprint_formset.is_valid()
    ):
        try:
            citizen = _save_citizen_with_related(form, formset, fingerprint_formset)
        except IntegrityError:
            messages.error(
                request,
                "A fingerprint you scanned is already registered to another person. "
                "Each finger must be unique.",
            )
        else:
            messages.success(request, f'Citizen "{citizen.full_name}" updated.')
            return redirect("citizens:detail", pk=citizen.pk)
    return render(
        request,
        "citizens/form.html",
        {
            "form": form,
            "formset": formset,
            "fingerprint_formset": fingerprint_formset,
            "action": "Edit",
            "citizen": citizen,
            "card": _build_form_card(citizen),
            **_family_form_context(citizen),
        },
    )


@staff_required
def generate_id(request, pk):
    """Assign (or return the existing) Citizen ID and return it as JSON."""
    citizen = get_object_or_404(Citizen, pk=pk)
    had_id = bool(citizen.registry_no)
    id_number = citizen.ensure_id_number()
    return JsonResponse({"id_number": id_number, "newly_generated": not had_id})


@staff_required
def citizen_id_card(request, pk):
    """Render a printable e-Bahagi ID card for a single citizen.
    Generates a Citizen ID if one has not been assigned yet."""
    citizen = get_object_or_404(Citizen, pk=pk)
    return render(
        request,
        "citizens/id_card.html",
        {"citizen": citizen, "card": _build_card(citizen)},
    )


@staff_required
def citizen_id_cards_all(request):
    """Render printable e-Bahagi ID cards for every citizen, one per page."""
    cards = [
        _build_card(citizen)
        for citizen in Citizen.objects.order_by("last_name", "first_name")
    ]
    return render(request, "citizens/id_cards_all.html", {"cards": cards})


@staff_required
def citizen_delete(request, pk):
    citizen = get_object_or_404(Citizen, pk=pk)
    if request.method == "POST":
        name = citizen.full_name
        citizen.delete()
        messages.success(request, f'Citizen "{name}" removed from the registry.')
        return redirect("citizens:list")
    return render(request, "citizens/confirm_delete.html", {"citizen": citizen})
