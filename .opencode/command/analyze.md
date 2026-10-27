---
description: Full senior-Django analysis of the codebase (or a given path/app): architecture, ORM, security, tests, deploy readiness
agent: plan
subtask: true
---
Act as a senior Django engineer performing a code analysis. Scope: `$ARGUMENTS` (if empty, analyze the whole repository).

Project layout:
!`git ls-files | grep -E '\.(py|html|md|toml|txt|json)$' | head -300`

Django system check:
!`python manage.py check 2>&1 | tail -20`

Pending model changes (should be none):
!`python manage.py makemigrations --check --dry-run 2>&1 | tail -20`

Lint snapshot:
!`ruff check . --statistics 2>&1 | tail -20`

Load skills as needed: `django-conventions`, `django-orm-performance`, `django-migrations`, `django-security-deploy`, `django-testing`, `stripe-integration`, `django-file-uploads`, `external-http-requests`. Read the actual code; do not guess. Do NOT modify files.

## Analyze these areas

1. **Architecture and structure**: app boundaries (domain vs technical layers), logic in views/forms/signals/templates instead of `services.py`/`selectors.py`, circular imports, custom user model, settings split, dead code, duplication.
2. **Models and database**: missing `related_name`/deliberate `on_delete`, missing constraints (`UniqueConstraint`, `CheckConstraint(condition=...)`), missing indexes for filters/ordering, float used for money, naive datetimes, fat `save()` overrides, `fields="__all__"`.
3. **Queries and performance**: N+1 patterns, missing `select_related`/`prefetch_related`, `len(qs)` vs `.count()`, unbounded querysets, Python loops that belong in the DB, unsafe counters (use `F()`), missing pagination, HTTP calls inside transactions.
4. **Security**: settings (`DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`, cookies, HSTS, CSRF origins), IDOR/unscoped querysets, missing auth/permission checks, `csrf_exempt`, `mark_safe`/`|safe`, raw SQL, open redirects, upload validation, secrets in repo.
5. **Stripe/payments**: webhook signature verification, idempotency (`StripeEvent`), amounts server-side, integer cents, fulfillment inside `transaction.atomic()`, no secrets in logs.
6. **External HTTP**: every `requests` call has `timeout`, no `verify=False`, error handling, SSRF risk.
7. **Migrations**: edited applied migrations, risky operations (lock/rewrite), data vs schema mixed, missing `AddIndexConcurrently` for large tables.
8. **Tests**: coverage gaps, missing permission tests (anonymous / wrong user / owner / staff), missing `django_assert_num_queries`, over-mocking the ORM, flaky patterns.
9. **Deployment readiness**: gunicorn command, whitenoise + `collectstatic`, `CONN_MAX_AGE`, logging, health check, `.env.example` completeness, `check --deploy` result.
10. **Dependencies**: pins consistent with `requirements.txt`, unused or missing packages, deprecation warnings.

## Output format (concise, no fluff)

1. **Summary**: 3-5 lines + overall health score /10 with one-line justification.
2. **Findings table** sorted by severity: `ID | Severity (Critical/High/Medium/Low) | Area | file:line | Problem | Fix`.
3. **Top 5 priorities** with effort estimate (S/M/L).
4. **Quick wins** (under 30 minutes each).
5. **Positive observations** (what is already done well).
6. **Suggested next commands** (e.g. `/perf-audit <view>`, `/check-deploy`, `/migrate`, `@django-security`).

Cite exact `file:line` for every finding. If something cannot be verified (no DB, no network), say so explicitly.
