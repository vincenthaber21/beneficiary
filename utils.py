"""Shared role-checking decorators for e-BAHAGI."""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def is_admin(user):
    if user.is_superuser:
        return True
    return hasattr(user, "profile") and user.profile.role == "admin"


def is_staff_or_admin(user):
    if user.is_superuser:
        return True
    return hasattr(user, "profile") and user.profile.role in ("admin", "staff")


def is_distributor(user):
    if not user.is_authenticated or user.is_superuser:
        return False
    return hasattr(user, "profile") and user.profile.role == "distributor"


def can_access_rfid(user):
    """Admin, staff, and ayuda distributors may use the ID / fingerprint tap page."""
    if user.is_superuser:
        return True
    return hasattr(user, "profile") and user.profile.role in (
        "admin",
        "staff",
        "distributor",
    )


def admin_required(func):
    @wraps(func)
    @login_required
    def inner(request, *args, **kwargs):
        if not is_admin(request.user):
            raise PermissionDenied
        return func(request, *args, **kwargs)
    return inner


def staff_required(func):
    @wraps(func)
    @login_required
    def inner(request, *args, **kwargs):
        if not is_staff_or_admin(request.user):
            raise PermissionDenied
        return func(request, *args, **kwargs)
    return inner


def rfid_access_required(func):
    """Allow admin, staff, and ayuda distributors on the RFID tap station."""
    @wraps(func)
    @login_required
    def inner(request, *args, **kwargs):
        if not can_access_rfid(request.user):
            raise PermissionDenied
        return func(request, *args, **kwargs)
    return inner
