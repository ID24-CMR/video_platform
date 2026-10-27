---
name: django-security-deploy
description: Production settings, secrets, security headers, auth hardening, gunicorn deployment and release checklist for Django. Load for deploy, hardening or security review.
---
# Security and Deployment

## Production settings (`config/settings/production.py`)
```python
from .base import *
DEBUG = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")   # only behind a trusted proxy
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")
```
Run `DJANGO_SETTINGS_MODULE=config.settings.production python manage.py check --deploy`.

## Secrets
Only from environment. `SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]` (crash if missing in production). `.env` gitignored. Rotate on leak (`SECRET_KEY_FALLBACKS` for graceful rotation).

## Authentication
- `AUTH_PASSWORD_VALIDATORS` enabled; use default hashers (PBKDF2) or add Argon2 via an extra dependency only if approved.
- `LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL` set. Rate-limit login and password reset (cache-based throttle in a decorator/middleware).
- Session: `SESSION_COOKIE_AGE`, `SESSION_SAVE_EVERY_REQUEST` only if needed.

## Authorization (IDOR prevention)
Always scope: `Order.objects.filter(user=request.user, pk=pk)` -> 404 otherwise. Never rely on hidden form fields or URL secrecy.

## Input/output
Forms validate. Raw SQL parameterized (`cursor.execute(sql, [param])`). No `mark_safe` on user data. Validate redirects with `url_has_allowed_host_and_scheme`. Use CSP (built in Django 6.x; check installed docs for `SECURE_CSP` settings) and avoid inline scripts.

## Gunicorn
```
gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-3} --timeout 30 --access-logfile - --error-logfile -
```
Workers ~ (2 x cores) + 1. Put nginx/platform proxy in front. `--max-requests 1000 --max-requests-jitter 100` to mitigate leaks.

## Release checklist
1. `pip install -r requirements.txt`
2. `python manage.py collectstatic --noinput`
3. `python manage.py migrate --noinput` (backward compatible)
4. Start gunicorn; smoke test `/healthz/`
5. Rollback plan: previous image + reversible migration notes.

## Logging
Structured console logging; `django.request` and `django.security` at WARNING+; never log secrets, tokens, card data, full Stripe payloads. Add Sentry only if approved.

## Dockerfile sketch
```dockerfile
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python manage.py collectstatic --noinput
USER nobody
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```
(`collectstatic` at build needs a dummy `DJANGO_SECRET_KEY`.)
