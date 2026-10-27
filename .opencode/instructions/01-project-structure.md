# Project Structure

```
.
├── manage.py
├── requirements.txt / requirements-dev.txt
├── .env / .env.example
├── pyproject.toml              # ruff, pytest, mypy config
├── config/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py             # shared, env-driven
│   │   ├── local.py            # DEBUG=True, debug toolbar
│   │   ├── production.py       # security flags, whitenoise, logging
│   │   └── test.py             # fast hashers, in-memory email
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── accounts/               # custom User model (from day one)
│   ├── core/                   # shared abstract models, utils, health check
│   ├── billing/                # Stripe integration
│   └── <domain>/
│       ├── models.py
│       ├── services.py         # writes / workflows (transaction.atomic)
│       ├── selectors.py        # reads / complex queries
│       ├── forms.py
│       ├── views.py            # thin
│       ├── urls.py
│       ├── admin.py
│       ├── tasks.py            # background tasks
│       ├── signals.py          # only decoupled notifications
│       ├── validators.py
│       ├── migrations/
│       ├── templates/<domain>/
│       └── tests/
│           ├── factories.py
│           ├── test_models.py
│           ├── test_services.py
│           ├── test_selectors.py
│           └── test_views.py
├── templates/                  # project-level base templates, errors
├── static/                     # source static assets
├── staticfiles/                # collectstatic output (gitignored)
├── media/                      # user uploads in dev only (gitignored)
└── tests/                      # cross-app / integration tests, conftest.py
```

## Rules

- One app per cohesive domain concept (`billing`, `accounts`, `orders`), **not** per technical layer.
- Apps live under `apps/`; `AppConfig.name = "apps.billing"`, `label = "billing"`.
- Custom user model `accounts.User` set via `AUTH_USER_MODEL` **before** the first migration.
- Views never contain business rules; they parse input, call a service/selector, return a response.
- Cross-app imports go through services/selectors, never through another app's private helpers.
- No circular imports: use string references for FKs (`"billing.Customer"`) and lazy imports in signals.
