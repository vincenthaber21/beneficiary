"""Middleware that records module opens and mutating actions for security audit."""
from django.utils.deprecation import MiddlewareMixin

from .audit import (
    infer_action,
    log_audit,
    resolve_module,
    should_skip_path,
)
from .models import AuditTrail


class AuditTrailMiddleware(MiddlewareMixin):
    """Log authenticated page opens and form submissions."""

    def process_response(self, request, response):
        try:
            self._maybe_log(request, response)
        except Exception:
            # Never break the request because of audit logging.
            pass
        return response

    def _maybe_log(self, request, response):
        path = request.path or ""
        if should_skip_path(path):
            return

        method = (request.method or "GET").upper()
        status = getattr(response, "status_code", 200)

        # Login / logout are handled by auth signals.
        if path.startswith("/accounts/login") or path.startswith("/accounts/logout"):
            return

        user = getattr(request, "user", None)
        is_auth = bool(user and user.is_authenticated)

        # Only track signed-in activity (except we already skip login here).
        if not is_auth:
            return

        # Skip redirects that would double-count (e.g. POST -> 302 -> GET).
        # Log successful page views and successful mutations.
        if method == "GET":
            if status >= 400:
                return
            # Prefer primary module entry points and meaningful pages;
            # skip tiny AJAX fragments if marked.
            if getattr(response, "streaming", False):
                return
            action = infer_action(method, path)
            module = resolve_module(path)
            log_audit(
                request=request,
                action=action,
                module=module,
                description=f"Opened {module}: {path}",
                success=True,
            )
            return

        if method in ("POST", "PUT", "PATCH", "DELETE"):
            action = infer_action(method, path)
            module = resolve_module(path)
            success = status < 400
            verb = dict(AuditTrail.Action.choices).get(action, action)
            log_audit(
                request=request,
                action=action,
                module=module,
                description=f"{verb} — {path}",
                success=success,
            )
