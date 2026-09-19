"""Fingerprint hash helpers (compatible with fingerprint_bridge aHash)."""


def hamming_hex(a: str, b: str) -> int:
    a = (a or "").strip().lower()
    b = (b or "").strip().lower()
    if not a or not b or len(a) != len(b):
        return 999
    try:
        return bin(int(a, 16) ^ int(b, 16)).count("1")
    except ValueError:
        return 999


def find_best_fingerprint(fp_hash: str, threshold: int = 10):
    """Return (CitizenFingerprint|None, distance)."""
    from .models import CitizenFingerprint

    fp_hash = (fp_hash or "").strip().lower()
    if not fp_hash:
        return None, 999

    best = None
    best_dist = 999
    for fp in CitizenFingerprint.objects.select_related("citizen").exclude(
        template_data=""
    ):
        dist = hamming_hex(fp_hash, fp.template_data)
        if dist < best_dist:
            best_dist = dist
            best = fp
    if best is not None and best_dist <= threshold:
        return best, best_dist
    return None, best_dist
