from types import SimpleNamespace

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from beneficiaries.views import _qr_svg
from utils import staff_required

from .forms import CitizenForm, CitizenFamilyFormSet, CitizenFingerprintFormSet
from .models import Citizen

_CREATE_INITIAL = {
    "municipality": "Bacnotan",
    "province": "La Union",
}


def _build_card(citizen):
    """Context dict for the shared e-Bahagi ID card template."""
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


def _save_citizen_with_related(form, family_formset, fingerprint_formset):
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

    qs = Citizen.objects.all()
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

    barangays = (
        Citizen.objects.exclude(barangay="")
        .values_list("barangay", flat=True)
        .distinct()
        .order_by("barangay")
    )

    context = {
        "citizens": qs,
        "total": qs.count(),
        "q": q,
        "status": status,
        "barangay": barangay,
        "barangays": barangays,
        "status_choices": Citizen.STATUS_CHOICES,
        "count_active": Citizen.objects.filter(status="active").count(),
        "count_inactive": Citizen.objects.exclude(status="active").count(),
    }
    return render(request, "citizens/list.html", context)


@staff_required
def citizen_detail(request, pk):
    citizen = get_object_or_404(
        Citizen.objects.prefetch_related("family_members__member", "fingerprints"),
        pk=pk,
    )
    return render(
        request,
        "citizens/detail.html",
        {"citizen": citizen, "card": _build_card(citizen)},
    )


@staff_required
def citizen_create(request):
    form = CitizenForm(request.POST or None, request.FILES or None, initial=_CREATE_INITIAL)
    formset = CitizenFamilyFormSet(request.POST or None, prefix="family")
    fingerprint_formset = CitizenFingerprintFormSet(
        request.POST or None, prefix="fp"
    )
    if (
        request.method == "POST"
        and form.is_valid()
        and formset.is_valid()
        and fingerprint_formset.is_valid()
    ):
        citizen = _save_citizen_with_related(form, formset, fingerprint_formset)
        messages.success(
            request,
            f'Citizen "{citizen.full_name}" registered ({citizen.registry_no}).',
        )
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
            "card": _build_card(None),
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
    fingerprint_formset = CitizenFingerprintFormSet(
        request.POST or None, instance=citizen, prefix="fp"
    )
    if (
        request.method == "POST"
        and form.is_valid()
        and formset.is_valid()
        and fingerprint_formset.is_valid()
    ):
        citizen = _save_citizen_with_related(form, formset, fingerprint_formset)
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
            "card": _build_card(citizen),
        },
    )


@staff_required
def citizen_id_card(request, pk):
    """Render a printable e-Bahagi ID card for a single citizen."""
    citizen = get_object_or_404(Citizen, pk=pk)
    return render(
        request,
        "citizens/id_card.html",
        {"citizen": citizen, "card": _build_card(citizen)},
    )


@staff_required
def citizen_delete(request, pk):
    citizen = get_object_or_404(Citizen, pk=pk)
    if request.method == "POST":
        name = citizen.full_name
        citizen.delete()
        messages.success(request, f'Citizen "{name}" removed from the registry.')
        return redirect("citizens:list")
    return render(request, "citizens/confirm_delete.html", {"citizen": citizen})
