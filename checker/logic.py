"""
Core beneficiary decision-tree logic (no Django dependencies).

    Is member of a valid class?
      No  -> Not qualified
      Yes -> Received grants within the last 3 months?
               Yes -> Not qualified
               No  -> Passes screen (QUALIFIED)

Valid beneficiary classes:
  Solo Parent, PWD, Senior Citizen, Construction Worker,
  Rice Farmer, Market Vendor, Tricycle Driver, Lactating Mother
"""

VALID_CLASSES = [
    "Solo Parent",
    "PWD",
    "Senior Citizen",
    "Construction Worker",
    "Rice Farmer",
    "Market Vendor",
    "Tricycle Driver",
    "Lactating Mother",
]

# Kept for settings / display compatibility; not used in qualification.
INCOME_THRESHOLD = 15000.00  # Php


def evaluate(beneficiary_class, received_grant_within_3_months, monthly_income=None,
             household_blocker_name=None):
    """Return a dict with the decision and the reason.

    Qualification is based on valid class and grant cooldown only.
    ``monthly_income`` is accepted for call-site compatibility but ignored.

    ``household_blocker_name`` – if set, a family member by that name has received
    a grant within the cooldown window, which disqualifies the whole household.
    """
    if beneficiary_class not in VALID_CLASSES:
        result, reason = "Not qualified", "Not a member of any valid beneficiary class."
    elif received_grant_within_3_months:
        result, reason = "Not qualified", "Received a grant within the last 3 months."
    elif household_blocker_name:
        result, reason = (
            "Not qualified",
            f"A family member ({household_blocker_name}) received a grant "
            f"within the last 3 months.",
        )
    else:
        result, reason = "Qualified", "Meets all requirements."

    return {
        "result": result,
        "reason": reason,
        "qualified": result == "Qualified",
    }
