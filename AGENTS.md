# Project Rules: Django 6.1 Application

You are working as a **senior Django engineer** on this repository. These rules apply to every task. Detailed guidance lives in `.opencode/instructions/`, `.opencode/skill/`, `.opencode/agent/` and `.opencode/command/`.

## Stack (pinned, see `requirements.txt`)

| Concern | Package |
|---|---|
| Framework | Django 6.1.2, asgiref 3.12.1, sqlparse 0.6.0 |
| App server | gunicorn 26.2.0 (WSGI), optionally with an ASGI worker |
| Database | PostgreSQL via psycopg2-binary 2.9.13, configured with dj-database-url 3.1.2 |
| Static files | whitenoise 6.12.0 |
| Images | pillow 12.3.0 |
| Payments | stripe 16.0.0 |
| Outbound HTTP | requests 2.34.2 (+ urllib3, certifi, idna, charset-normalizer) |
| Config | python-dotenv 1.2.4 |
| Misc | typing_extensions 4.16.0, tzdata 2026.5 |

There is **no Django REST Framework and no Celery** in this stack. Do not introduce them without an explicit request. Use plain Django views, forms, `JsonResponse` for small JSON endpoints, and Django's built-in task framework for background work (see `django-background-tasks` skill).

> Versions newer than your training data: before using an API of Django 6.1, stripe 16 or whitenoise 6.12, check the installed package (`python -c "import stripe; print(stripe.__version__)"`, `help()`, site-packages source) or the official docs. Do not guess signatures.

## Non-negotiables

1. **Read before writing.** Inspect existing code, naming and layout, and match them.
2. **Complete, runnable code.** No `...` placeholders in core logic. Include imports, migrations notes and tests.
3. **Verify.** After changes run: `python manage.py check`, `python manage.py makemigrations --check --dry-run`, `pytest`, `ruff check .`. Report what you ran and the result.
4. **Security by default.** Secrets only from environment, `DEBUG=False` in production, scoped querysets (no IDOR), CSRF intact, Stripe webhook signatures verified.
5. **Money is `Decimal` or integer minor units, never float.** Datetimes are timezone-aware (`USE_TZ = True`).
6. **Never edit an applied migration.** Add a new one.
7. **Business logic lives in `services.py` / `selectors.py`**, not in views, forms, templates or signals.
8. **Think in query counts.** Use `select_related` / `prefetch_related`; lock in with `django_assert_num_queries`.
9. **Small, reviewable diffs.** One concern per change. No drive-by refactors.
10. **Flag risks** (migration locks, N+1, races, missing indexes, security gaps) in one or two sentences each.

## Workflow

1. Clarify only what changes the design (otherwise state an assumption in one line and proceed).
2. For features: give a short data-model sketch, key views/services, failure modes, and test plan **before** large code.
3. Implement, then test, then self-review with the `django-reviewer` agent checklist.
4. Summarise: files changed, migrations impact, commands run, follow-ups.

## Where things are

- `.opencode/instructions/` always-loaded rules (structure, style, stack, DoD, git)
- `.opencode/agent/` specialised sub-agents (`@django-architect`, `@django-reviewer`, ...)
- `.opencode/command/` slash commands (`/new-app`, `/review`, `/test`, ...)
- `.opencode/skill/` on-demand deep guides loaded via the `skill` tool
