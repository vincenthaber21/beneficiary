from .models import SystemLogo, SystemSetting

DEFAULT_ORG_NAME = "Humanitarian Assistance Grant Management"


def system_branding(request):
    org_name = SystemSetting.get("org_name", DEFAULT_ORG_NAME) or DEFAULT_ORG_NAME
    return {
        "system_logo": SystemLogo.load(),
        "org_name": org_name,
    }
