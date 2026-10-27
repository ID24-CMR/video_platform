---
description: Exhaustive audit of the WHOLE codebase (security, ORM, migrations, Stripe, tests, deploy, deps). Writes AUDIT_REPORT.md
agent: build
---
Perform a complete, evidence-based audit of the entire repository as a senior Django engineer. Optional focus: `$ARGUMENTS` (if empty, audit everything).

**Hard rule: do NOT modify application code, migrations, settings or tests.** The only file you may create is `AUDIT_REPORT.md` in the repo root (and temporary files under `/tmp`).

## Phase 0: Inventory
Tracked files: !`git ls-files | head -500`

Python files and size: !`git ls-files '*.py' | xargs wc -l 2>/dev/null | sort -n | tail -30`

Apps and URLs: !`grep -rn "INSTALLED_APPS\|path(\|re_path(\|include(" --include=*.py . 2>/dev/null | grep -v "/migrations/\|/tests/\|venv" | head -150`

Recent history: !`git log --oneline -20 2>/dev/null`

## Phase 1: Automated checks (run and record each result)
1. `python manage.py check`
2. `DJANGO_SETTINGS_MODULE=config.settings.production python manage.py check --deploy`
3. `python manage.py makemigrations --check --dry-run`
4. `python manage.py showmigrations --plan | grep "\[ \]"` (unapplied)
5. `ruff check . --statistics` and `ruff format --check .`
6. `mypy .` if configured
7. `pytest -q --cov --cov-report=term-missing` (skip coverage flags if `pytest-cov` unavailable)
8. `pip check` and `pip list --outdated`
9. `python -W error::DeprecationWarning manage.py check`
10. Secret scan: `grep -rEn "(sk_live|sk_test|whsec_|SECRET_KEY\s*=\s*['\"]|password\s*=\s*['\"])" --include=*.py --include=*.env* --include=*.json --include=*.yml . | grep -v ".env.example"`

If a command cannot run (no DB, missing package), record `NOT VERIFIED` with the reason. Never claim a pass you did not observe.

## Phase 2: Delegate deep reviews (use subagents, then merge findings)
- `@django-security`: settings, auth/authz, IDOR, CSRF, uploads, redirects, Stripe webhook, headers.
- `@django-migrations`: every migration for lock/rewrite risk, edited-applied migrations, data vs schema mixing, reversibility.
- `@stripe-payments`: signature verification, idempotency (`StripeEvent`), server-side amounts, integer cents, `on_commit`, secrets in logs.
- `@django-reviewer`: layering (logic in views/signals), models, forms (`fields="__all__"`), error handling.
- `@django-tester`: coverage gaps, missing permission-matrix tests, missing `django_assert_num_queries`, over-mocking, flaky patterns (analysis only, write no tests).

## Phase 3: Manual sweeps (read the code, cite file:line)
- **Models**: `related_name`, `on_delete` (PROTECT for money/audit), `UniqueConstraint`/`CheckConstraint(condition=...)`, indexes vs actual filters/ordering, float for money, naive datetimes, fat `save()`, signals with business logic.
- **Queries**: N+1, missing `select_related`/`prefetch_related`, `len(qs)`, unbounded querysets, Python-side aggregation, non-atomic counters (use `F()`), multi-step writes without `transaction.atomic()`, races (`get_or_create` without unique constraint), network calls inside transactions.
- **Views/URLs**: unscoped `get_object_or_404`, missing `LoginRequiredMixin`/permissions, `csrf_exempt`, `mark_safe`/`|safe`, raw SQL, `request.GET` straight into queries, open redirects, missing pagination.
- **Templates**: unescaped output, missing `{% csrf_token %}`, inline scripts vs CSP, N+1 hidden in template loops.
- **Uploads/Pillow**: size/type validation, random filenames, `MAX_IMAGE_PIXELS`, storage location.
- **External HTTP (`requests`)**: `timeout=` on every call, `verify=False`, retries only on idempotent methods, SSRF on user URLs, error handling.
- **Static/media (whitenoise)**: middleware order, manifest storage, `collectstatic`, media not served by whitenoise.
- **Settings/ops**: env-driven secrets, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, HSTS and cookie flags, `CONN_MAX_AGE`/health checks, logging (no secrets), `/healthz/`, gunicorn config, `.env.example` completeness, `.gitignore` coverage.
- **Dependencies**: compare imports with `requirements.txt` (unused / missing), transitive pin consistency (urllib3, certifi, idna, charset-normalizer), end-of-life or deprecated APIs for Django 6.1.

## Phase 4: Write `AUDIT_REPORT.md`
Use exactly this structure:

1. **Executive summary**: scope, date, commit hash, overall score /10 per area (Architecture, Data/ORM, Security, Payments, Migrations, Tests, Performance, Deploy, Dependencies), and a go / no-go statement for production.
2. **Automated check results**: table `Check | Result | Notes` (use PASS / FAIL / NOT VERIFIED).
3. **Findings**: table sorted by severity `ID | Severity (Critical/High/Medium/Low/Info) | Area | file:line | Problem | Impact | Recommended fix | Effort (S/M/L)`.
4. **Top 10 priorities** in fix order, with rationale.
5. **Quick wins** (< 30 min each).
6. **Migration & data risks** needing a deploy plan.
7. **Test gaps** and the exact tests to add.
8. **What is done well.**
9. **Remediation roadmap**: Week 1 / Week 2 / Later, mapped to commands (`/perf-audit`, `/migrate`, `/add-stripe-webhook`, `/test`, `/check-deploy`).
10. **Appendix**: commands run, versions, files reviewed, items not verified.

Every finding must cite `file:line` and be reproducible. Do not pad with generic advice. Finish by printing the executive summary and the Top 10 in chat, and the path of the report.
