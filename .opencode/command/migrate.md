---
description: Create and safety-review a migration
agent: django-migrations
subtask: true
---
Create and review migration(s) for pending model changes. Scope: $ARGUMENTS

Pending changes: !`python manage.py makemigrations --dry-run -v 1`

Show the generated SQL, classify lock/rewrite risk, and give the deploy plan.
