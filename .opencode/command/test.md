---
description: Run the test suite, lint and Django checks and summarise failures
agent: build
---
Run, in order, and report results concisely:

1. `python manage.py check`
2. `python manage.py makemigrations --check --dry-run`
3. `ruff check .` and `ruff format --check .`
4. `pytest -q $ARGUMENTS`

If anything fails: identify root cause, fix it, re-run. Do not weaken or delete tests to make them pass.
