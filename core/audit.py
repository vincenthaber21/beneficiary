"""Helpers for writing security audit trail entries."""
from __future__ import annotations

from typing import Optional

from django.http import HttpRequest


MODULE_PREFIXES = (
    ("/admin/", "Administration"),
    ("/audit-trails/", "Audit Trails"),
    ("/programs/", "Programs"),
    ("/beneficiaries/", "Beneficiaries"),
    ("/citizens/", "Citizens"),
    ("/records/", "Records"),
    ("/reports/", "Reports"),
    ("/users/", "User Management"),
    ("/settings/", "Settings"),
    ("/check/", "Eligibility Checker"),
    ("/accounts/", "Accounts"),
)

SKIP_PREFIXES = (
    "/static/",
    "/media/",
    "/favicon",
    "/__debug__/",
)


def get_client_ip(request: HttpRequest) -> Optional[str]:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip() or None
    return request.META.get("REMOTE_ADDR") or None


def resolve_module(path: str) -> str:
    if path in ("/", ""):
        return "Dashboard"
    for prefix, name in MODULE_PREFIXES:
        if path.startswith(prefix):
            return name
    return "System"


def should_skip_path(path: str) -> bool:
    if any(path.startswith(p) for p in SKIP_PREFIXES):
        return True
    # Avoid noisy self-logging while browsing audit trails.
    if "/admin/core/audittrail" in path or path.startswith("/audit-trails"):
        return True
    return False


def infer_action(method: str, path: str) -> str:
    from .models import AuditTrail

    lower = path.lower()
    if method == "GET":
        if any(k in lower for k in ("export", "download", "print", "id_card", "id-card")):
            return AuditTrail.Action.EXPORT
        return AuditTrail.Action.MODULE_OPEN

    if any(k in lower for k in ("delete", "remove")):
        return AuditTrail.Action.DELETE
    if any(k in lower for k in ("import",)):
        return AuditTrail.Action.IMPORT
    if any(k in lower for k in ("backup",)):
        return AuditTrail.Action.BACKUP
    if any(k in lower for k in ("restore",)):
        return AuditTrail.Action.RESTORE
    if any(k in lower for k in ("edit", "update", "change")):
        return AuditTrail.Action.UPDATE
    if any(k in lower for k in ("add", "create", "new")):
        return AuditTrail.Action.CREATE
    if method in ("POST", "PUT", "PATCH"):
        return AuditTrail.Action.UPDATE
    if method == "DELETE":
        return AuditTrail.Action.DELETE
    return AuditTrail.Action.OTHER


def action_verb(action: str) -> str:
    from .models import AuditTrail

    return {
        AuditTrail.Action.LOGIN: "Logged in",
        AuditTrail.Action.LOGOUT: "Logged out",
        AuditTrail.Action.LOGIN_FAILED: "Failed login attempt",
        AuditTrail.Action.MODULE_OPEN: "Opened",
        AuditTrail.Action.CREATE: "Created / submitted in",
        AuditTrail.Action.UPDATE: "Updated / submitted in",
        AuditTrail.Action.DELETE: "Deleted in",
        AuditTrail.Action.VIEW: "Viewed",
        AuditTrail.Action.EXPORT: "Exported / printed from",
        AuditTrail.Action.IMPORT: "Imported into",
        AuditTrail.Action.BACKUP: "Ran backup in",
        AuditTrail.Action.RESTORE: "Ran restore in",
        AuditTrail.Action.OTHER: "Action in",
    }.get(action, "Action in")


def log_audit(
    *,
    request: Optional[HttpRequest] = None,
    user=None,
    username: str = "",
    action: str,
    module: str = "",
    description: str = "",
    path: str = "",
    method: str = "",
    success: bool = True,
) -> None:
    from .models import AuditTrail

    ip = None
    ua = ""
    if request is not None:
        ip = get_client_ip(request)
        ua = (request.META.get("HTTP_USER_AGENT") or "")[:400]
        path = path or (request.path or "")
        method = method or (request.method or "")
        if user is None and getattr(request, "user", None) is not None:
            if request.user.is_authenticated:
                user = request.user
        if not username and user is not None and getattr(user, "is_authenticated", False):
            username = user.get_username()

    if not module and path:
        module = resolve_module(path)

    if not description:
        description = f"{action_verb(action)} {module}".strip()

    AuditTrail.objects.create(
        user=user if user is not None and getattr(user, "is_authenticated", False) else None,
        username=username or "",
        action=action,
        module=module or "",
        description=description[:500],
        path=(path or "")[:500],
        method=(method or "")[:10],
        ip_address=ip,
        user_agent=ua,
        success=success,
    )
