from .models import SystemLogo


def system_branding(request):
    return {"system_logo": SystemLogo.load()}
