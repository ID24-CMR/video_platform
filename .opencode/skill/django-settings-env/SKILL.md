---
name: django-settings-env
description: Environment-driven Django settings using python-dotenv and dj-database-url, split settings, whitenoise and logging. Load when editing settings.
---
# Settings and Environment

## `config/settings/base.py`
```python
import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")          # no-op in production if file absent

def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}

def env_list(name: str, default: str = "") -> list[str]:
    return [v.strip() for v in os.getenv(name, default).split(",") if v.strip()]

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")

DATABASES = {
    "default": dj_database_url.config(env="DATABASE_URL", conn_max_age=60, conn_health_checks=True)
}

AUTH_USER_MODEL = "accounts.User"
USE_TZ = True
TIME_ZONE = "UTC"
LANGUAGE_CODE = "en-us"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
SITE_URL = os.getenv("SITE_URL", "http://localhost:8000")
```
Note: Django 4.2+ uses `STORAGES`; the legacy `STATICFILES_STORAGE` setting is gone.

## `local.py`
`DEBUG=True`, `ALLOWED_HOSTS=["*"]` only locally, console email backend, debug toolbar if installed, whitenoise `autorefresh` not needed (runserver serves static).

## `manage.py`, `wsgi.py`, `asgi.py`
Default `DJANGO_SETTINGS_MODULE` to `config.settings.local` in `manage.py`, to `config.settings.production` in `wsgi.py`/`asgi.py`.

## Logging
```python
LOGGING = {
  "version": 1, "disable_existing_loggers": False,
  "formatters": {"std": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}},
  "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "std"}},
  "root": {"handlers": ["console"], "level": os.getenv("LOG_LEVEL", "INFO")},
}
```

## Rules
Every new env var goes in `.env.example` with a safe placeholder. Fail fast on missing required vars in production.
