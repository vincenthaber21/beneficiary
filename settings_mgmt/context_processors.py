from .models import SystemLogo, SystemSetting

DEFAULT_ORG_NAME = SystemLogo.DEFAULT_ORG_NAME


def system_branding(request):
    logo = SystemLogo.load()
    org_name = (logo.org_name or "").strip()
    if not org_name:
        org_name = SystemSetting.get("org_name", DEFAULT_ORG_NAME) or DEFAULT_ORG_NAME
    return {
        "system_logo": logo,
        "org_name": org_name,
    }
