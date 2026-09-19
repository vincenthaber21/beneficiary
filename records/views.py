import json
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Sum
from utils import staff_required
from programs.models import AssistanceProgram
from .models import GrantRecord
from .forms import GrantRecordForm


def _program_budgets():
    """Map of program id -> budget figures for the add/edit form JS."""
    programs = AssistanceProgram.objects.annotate(
        released=Sum("grants__amount", filter=Q(grants__status="released")),
    )
    data = {}
    for p in programs:
        budget = p.budget or Decimal("0")
        released = p.released or Decimal("0")
        data[p.pk] = {
            "name": p.name,
            "budget": float(budget),
            "released": float(released),
            "available": float(budget - released),
        }
    return json.dumps(data)


@staff_required
def record_list(request):
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    qs = GrantRecord.objects.select_related("beneficiary", "program", "granted_by")
    if q:
        qs = qs.filter(
            Q(beneficiary__last_name__icontains=q) |
            Q(beneficiary__first_name__icontains=q) |
            Q(program__name__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)
    records = list(qs)
    total_released  = sum(r.amount for r in records if r.status == "released")
    count_released  = sum(1 for r in records if r.status == "released")
    count_pending   = sum(1 for r in records if r.status == "pending")
    count_cancelled = sum(1 for r in records if r.status == "cancelled")
    return render(request, "records/list.html", {
        "records": records, "q": q, "status": status,
        "status_choices": GrantRecord.STATUS_CHOICES,
        "total_released": total_released,
        "count_released": count_released,
        "count_pending": count_pending,
        "count_cancelled": count_cancelled,
    })


@staff_required
def record_create(request):
    initial = {}
    ben_id = request.GET.get("beneficiary")
    if ben_id:
        initial["beneficiary"] = ben_id
    form = GrantRecordForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        record = form.save(commit=False)
        record.granted_by = request.user
        record.save()
        messages.success(request, "Grant record created successfully.")
        return redirect("records:list")
    return render(request, "records/form.html", {
        "form": form, "action": "Add", "program_budgets": _program_budgets(),
    })


@staff_required
def record_update(request, pk):
    record = get_object_or_404(GrantRecord, pk=pk)
    form = GrantRecordForm(request.POST or None, instance=record)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Record updated successfully.")
        return redirect("records:list")
    return render(request, "records/form.html", {
        "form": form, "action": "Edit", "record": record,
        "program_budgets": _program_budgets(),
    })


@staff_required
def record_delete(request, pk):
    record = get_object_or_404(GrantRecord, pk=pk)
    if request.method == "POST":
        record.delete()
        messages.success(request, "Record deleted.")
        return redirect("records:list")
    return render(request, "records/confirm_delete.html", {"record": record})
