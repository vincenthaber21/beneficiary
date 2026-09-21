"""
Django settings for beneficiary_project (e-BAHAGI).
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "SESSION_SECRET",
    "django-insecure-change-me-for-production-0123456789abcdef",
)

DEBUG = True
ALLOWED_HOSTS = [
    '*',  # Wildcard for development (remove in production)
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
]

CSRF_TRUSTED_ORIGINS = [
    "https://*.replit.dev",
    "https://*.repl.co",
    "https://*.riker.replit.dev",
    "https://*.replit.app",
    "http://localhost",
    "http://127.0.0.1",
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Project apps
    "checker",
    "core.apps.CoreConfig",
    "programs",
    "beneficiaries",
    "records",
    "reports",
    "user_mgmt",
    "settings_mgmt",
    "citizens.apps.CitizensConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.DistributorAccessMiddleware",
    "core.middleware.AuditTrailMiddleware",
]

ROOT_URLCONF = "beneficiary_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "settings_mgmt.context_processors.system_branding",
            ],
        },
    },
]

WSGI_APPLICATION = "beneficiary_project.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# In-memory cache for citizen search / available-count on beneficiary forms.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "ebahagi-cache",
        "TIMEOUT": 300,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Manila"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Allow large backup uploads (database + media zip) for admin restore.
DATA_UPLOAD_MAX_MEMORY_SIZE = 512 * 1024 * 1024  # 512 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # stream larger files to disk

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"
