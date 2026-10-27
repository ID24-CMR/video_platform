---
description: Pre-release checklist and release notes
agent: build
---
Prepare release `$ARGUMENTS`:

1. `/test` full pass, `check --deploy` with production settings.
2. List unapplied migrations: `python manage.py showmigrations --plan | grep "\[ \]"`; classify risk.
3. Confirm `collectstatic --noinput` succeeds (whitenoise manifest).
4. Confirm new env vars are in `.env.example` and deployment docs.
5. Generate release notes from `git log` since last tag, grouped by feat/fix/chore.
6. Provide deploy order: build -> migrate (backward-compatible first) -> deploy -> smoke test `/healthz/` -> rollback plan.
