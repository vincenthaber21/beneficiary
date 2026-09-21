"""Fingerprint hash helpers (compatible with fingerprint_bridge aHash)."""

# Same threshold used at the ID / Fingerprint Tap station.
DUPLICATE_THRESHOLD = 10


def hamming_hex(a: str, b: str) -> int:
    a = (a or "").strip().lower()
    b = (b or "").strip().lower()
    if not a or not b or len(a) != len(b):
        return 999
    try:
        return bin(int(a, 16) ^ int(b, 16)).count("1")
    except ValueError:
        return 999


def normalize_template(fp_hash: str) -> str:
    return (fp_hash or "").strip().lower()


def find_best_fingerprint(fp_hash: str, threshold: int = DUPLICATE_THRESHOLD):
    """Return (CitizenFingerprint|None, distance)."""
    from .models import CitizenFingerprint

    return _find_best(CitizenFingerprint, "citizen", fp_hash, threshold)


def find_best_beneficiary_fingerprint(fp_hash: str, threshold: int = DUPLICATE_THRESHOLD):
    """Return (BeneficiaryFingerprint|None, distance)."""
    from beneficiaries.models import BeneficiaryFingerprint

    return _find_best(BeneficiaryFingerprint, "beneficiary", fp_hash, threshold)


def _find_best(model, related: str, fp_hash: str, threshold: int = DUPLICATE_THRESHOLD):
    fp_hash = normalize_template(fp_hash)
    if not fp_hash:
        return None, 999

    best = None
    best_dist = 999
    for fp in model.objects.select_related(related).exclude(template_data=""):
        dist = hamming_hex(fp_hash, fp.template_data)
        if dist < best_dist:
            best_dist = dist
            best = fp
    if best is not None and best_dist <= threshold:
        return best, best_dist
    return None, best_dist


def find_duplicate_fingerprint(
    fp_hash: str,
    *,
    threshold: int = DUPLICATE_THRESHOLD,
    exclude_citizen_fp_id=None,
    exclude_beneficiary_fp_id=None,
):
    """
    Check whether this template is already enrolled to anyone.

    Returns (owner_label, fingerprint, distance) or (None, None, 999).
    owner_label is a short human-readable string like 'citizen Juan Dela Cruz'.
    """
    from beneficiaries.models import BeneficiaryFingerprint
    from .models import CitizenFingerprint

    fp_hash = normalize_template(fp_hash)
    if not fp_hash:
        return None, None, 999

    best = None
    best_label = None
    best_dist = 999

    citizen_qs = CitizenFingerprint.objects.select_related("citizen").exclude(
        template_data=""
    )
    if exclude_citizen_fp_id:
        citizen_qs = citizen_qs.exclude(pk=exclude_citizen_fp_id)
    for fp in citizen_qs:
        dist = hamming_hex(fp_hash, fp.template_data)
        if dist < best_dist:
            best_dist = dist
            best = fp
            best_label = (
                f'citizen "{fp.citizen}" ({fp.get_finger_display()})'
            )

    beneficiary_qs = BeneficiaryFingerprint.objects.select_related(
        "beneficiary"
    ).exclude(template_data="")
    if exclude_beneficiary_fp_id:
        beneficiary_qs = beneficiary_qs.exclude(pk=exclude_beneficiary_fp_id)
    for fp in beneficiary_qs:
        dist = hamming_hex(fp_hash, fp.template_data)
        if dist < best_dist:
            best_dist = dist
            best = fp
            best_label = (
                f'beneficiary "{fp.beneficiary}" ({fp.get_finger_display()})'
            )

    if best is not None and best_dist <= threshold:
        return best_label, best, best_dist
    return None, None, best_dist


def uniqueness_report(
    fp_hash: str,
    *,
    threshold: int = DUPLICATE_THRESHOLD,
    exclude_citizen_fp_id=None,
    exclude_beneficiary_fp_id=None,
):
    """JSON-friendly uniqueness check used by the live Scan action."""
    from django.urls import reverse

    from beneficiaries.models import BeneficiaryFingerprint

    owner_label, fp, dist = find_duplicate_fingerprint(
        fp_hash,
        threshold=threshold,
        exclude_citizen_fp_id=exclude_citizen_fp_id,
        exclude_beneficiary_fp_id=exclude_beneficiary_fp_id,
    )
    if not owner_label or fp is None:
        return {"ok": True, "unique": True}

    if isinstance(fp, BeneficiaryFingerprint):
        kind = "beneficiary"
        owner_id = fp.beneficiary_id
        owner_name = str(fp.beneficiary)
        owner_url = reverse("beneficiaries:detail", args=[owner_id])
    else:
        kind = "citizen"
        owner_id = fp.citizen_id
        owner_name = str(fp.citizen)
        owner_url = reverse("citizens:detail", args=[owner_id])

    return {
        "ok": True,
        "unique": False,
        "kind": kind,
        "owner_id": owner_id,
        "owner_name": owner_name,
        "finger": fp.get_finger_display(),
        "owner": owner_label,
        "owner_url": owner_url,
        "distance": dist,
        "message": (
            f"This fingerprint is already registered to {owner_label}. "
            "Each person must have a unique fingerprint on every finger."
        ),
    }
