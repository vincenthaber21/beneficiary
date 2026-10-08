from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
from utils import admin_required
from beneficiaries.models import Beneficiary
from checker.logic import VALID_CLASSES
from records.models import GrantRecord
from .models import AssistanceProgram
from .forms import AssistanceProgramForm


def _annotate_budget(programs):
    """Attach ``spent`` and ``remaining`` to each program.

    ``spent`` is the total of released grant amounts recorded against the
    program (matching the Records page's ``Amount``); ``remaining`` is the
    program budget minus what has been spent.
    """
    spent_by_program = {
        row["program_id"]: row["total"]
        for row in GrantRecord.objects
        .filter(status="released")
        .values("program_id")
        .annotate(total=Sum("amount"))
    }
    for program in programs:
        program.spent = spent_by_program.get(program.pk) or Decimal("0")
        program.remaining = program.budget - program.spent
    return programs


def _annotate_eligible_counts(programs):
    """Attach ``eligible_count`` to each program using per-program cooldown + threshold."""
    for program in programs:
        cutoff = timezone.now().date() - timedelta(days=program.grant_cooldown_months * 30)
        recent_ids = set(
            GrantRecord.objects.filter(
                status="released", date_granted__gte=cutoff
            ).values_list("beneficiary_id", flat=True)
        )
        program.eligible_count = (
            Beneficiary.objects
            .filter(
                is_active=True,
                beneficiary_class__in=VALID_CLASSES,
            )
            .exclude(pk__in=recent_ids)
            .count()
        )
    return programs


@admin_required
def program_list(request):
    programs = list(AssistanceProgram.objects.all())
    _annotate_eligible_counts(programs)
    _annotate_budget(programs)
    return render(request, "programs/list.html", {"programs": programs})


@admin_required
def program_create(request):
    form = AssistanceProgramForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Assistance program created successfully.")
        return redirect("programs:list")
    return render(request, "programs/form.html", {"form": form, "action": "Add"})


@admin_required
def program_update(request, pk):
    program = get_object_or_404(AssistanceProgram, pk=pk)
    form = AssistanceProgramForm(request.POST or None, instance=program)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Program updated successfully.")
        return redirect("programs:list")
    return render(request, "programs/form.html", {"form": form, "action": "Edit", "program": program})


@admin_required
def program_delete(request, pk):
    program = get_object_or_404(AssistanceProgram, pk=pk)
    if request.method == "POST":
        program.delete()
        messages.success(request, "Program deleted.")
        return redirect("programs:list")
    return render(request, "programs/confirm_delete.html", {"program": program})
