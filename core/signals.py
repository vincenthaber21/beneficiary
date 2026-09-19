"""Auth signal handlers for login / logout / failed login audit entries."""
from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver

from .audit import log_audit
from .models import AuditTrail


@receiver(user_logged_in)
def audit_user_logged_in(sender, request, user, **kwargs):
    log_audit(
        request=request,
        user=user,
        username=user.get_username(),
        action=AuditTrail.Action.LOGIN,
        module="Accounts",
        description=f"User '{user.get_username()}' logged in",
        success=True,
    )


@receiver(user_logged_out)
def audit_user_logged_out(sender, request, user, **kwargs):
    username = ""
    if user is not None and getattr(user, "is_authenticated", False):
        username = user.get_username()
    elif request is not None:
        # Fallback if session already cleared.
        username = getattr(getattr(request, "user", None), "username", "") or ""
    log_audit(
        request=request,
        user=user if user is not None and getattr(user, "pk", None) else None,
        username=username or "unknown",
        action=AuditTrail.Action.LOGOUT,
        module="Accounts",
        description=f"User '{username or 'unknown'}' logged out",
        success=True,
    )


@receiver(user_login_failed)
def audit_user_login_failed(sender, credentials, request, **kwargs):
    username = ""
    if isinstance(credentials, dict):
        username = credentials.get("username") or credentials.get("email") or ""
    log_audit(
        request=request,
        username=str(username)[:150],
        action=AuditTrail.Action.LOGIN_FAILED,
        module="Accounts",
        description=f"Failed login attempt for '{username or 'unknown'}'",
        success=False,
    )
