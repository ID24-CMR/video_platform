---
description: Scaffold a new Django app with services/selectors/tests layout
agent: build
---
Create a new Django app named `$ARGUMENTS` under `apps/`.

Steps:
1. Run `python manage.py startapp $ARGUMENTS apps/$ARGUMENTS` (create the directory first).
2. Set `name = "apps.$ARGUMENTS"` and `label = "$ARGUMENTS"` in `apps.py`.
3. Add to `INSTALLED_APPS` in `config/settings/base.py`.
4. Create: `services.py`, `selectors.py`, `forms.py`, `urls.py` (with `app_name`), `tests/` package with `factories.py`, `test_models.py`, `test_services.py`, `test_views.py`, and `templates/$ARGUMENTS/`.
5. Include URLs in `config/urls.py`.
6. Run `python manage.py check` and `pytest`.

Follow `.opencode/instructions/01-project-structure.md`. Report files created.
