# Definition of Done

A task is done only when all apply:

- [ ] `python manage.py check` passes (and `check --deploy` for production-settings changes)
- [ ] `python manage.py makemigrations --check --dry-run` reports no missing migrations
- [ ] New/changed behavior has tests (service, selector, view, permission cases)
- [ ] `pytest` green; list endpoints have a `django_assert_num_queries` test
- [ ] `ruff check .` and `ruff format --check .` clean
- [ ] Migrations reviewed for locking/rewrite risk; reversible where possible
- [ ] No secrets, keys or PII in code, logs or fixtures
- [ ] Permissions tested: anonymous, wrong user, correct user, staff
- [ ] Docs/README/`.env.example` updated for new settings or env vars
- [ ] Summary written: files changed, migration impact, commands run, risks/follow-ups
