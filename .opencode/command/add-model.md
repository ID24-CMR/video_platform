---
description: Add a model with constraints, indexes, admin, factory and tests
agent: build
---
Add this model: $ARGUMENTS

Requirements: explicit `related_name` and `on_delete`; `TextChoices` for enums; `TimeStampedModel` base if present; DB-level constraints (`UniqueConstraint`, `CheckConstraint(condition=...)`) and indexes matching expected queries; `__str__`; admin registration with `list_select_related`, `search_fields`, `list_filter`; factory_boy factory; model + constraint tests.

Then run `python manage.py makemigrations <app> --name <meaningful_name>`, inspect with `sqlmigrate`, and state the migration impact (safe / multi-step). Run `check`, `pytest`, `ruff`.
