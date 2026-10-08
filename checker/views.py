from django.shortcuts import render
from .forms import BeneficiaryForm
from .logic import evaluate


def check(request):
    result = None
    if request.method == "POST":
        form = BeneficiaryForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            result = evaluate(
                beneficiary_class=data["beneficiary_class"],
                received_grant_within_3_months=data["received_grant_within_3_months"],
            )
    else:
        form = BeneficiaryForm()

    return render(request, "checker/check.html", {"form": form, "result": result})
