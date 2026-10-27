---
description: Run production readiness checks and fix findings
agent: django-security
subtask: true
---
Run `DJANGO_SETTINGS_MODULE=config.settings.production python manage.py check --deploy` and audit production settings against the `django-security-deploy` skill. Output: findings by severity, exact settings diffs to fix them, plus a gunicorn/whitenoise/collectstatic/migrate release checklist.
