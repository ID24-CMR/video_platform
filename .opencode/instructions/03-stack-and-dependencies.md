# Stack and Dependency Rules

Pinned in `requirements.txt`. Do not bump, add or remove packages without being asked.

## Adding a dependency
1. Justify it in one sentence (what stdlib/Django cannot do).
2. Pin exact version (`==`). Production deps in `requirements.txt`, tooling in `requirements-dev.txt`.
3. Check license and maintenance status. Prefer packages with recent releases.

## Package-specific rules

- **Django 6.1.2**: use built-in features first (CSP middleware, template partials, `django.tasks`, `GeneratedField`, `db_default`, `constraints` with `condition=`). Run `python -W error::DeprecationWarning manage.py check` when upgrading.
- **asgiref**: used by Django internally. Use `sync_to_async` / `async_to_sync` only when needed; never call blocking code in async views without it.
- **gunicorn**: `gunicorn config.wsgi:application --workers $WEB_CONCURRENCY --timeout 30 --access-logfile -`. For async views use `-k uvicorn_worker.UvicornWorker` only if a compatible worker package is added deliberately.
- **psycopg2-binary**: acceptable for dev/small deployments. For heavy production consider building `psycopg2` from source. Use `CONN_MAX_AGE` (e.g. 60) with sync workers, and `CONN_HEALTH_CHECKS = True`.
- **dj-database-url**: `dj_database_url.config(env="DATABASE_URL", conn_max_age=60, conn_health_checks=True)` (check the installed signature).
- **python-dotenv**: load `.env` in `manage.py`/`config/settings/base.py` for local only; production uses real environment variables.
- **whitenoise**: middleware directly after `SecurityMiddleware`; storage `whitenoise.storage.CompressedManifestStaticFilesStorage`. See skill `whitenoise-static-media`.
- **pillow**: only for `ImageField` and image processing; always validate uploads. See skill `django-file-uploads`.
- **requests**: always pass `timeout=`; use a `Session` with retries via `urllib3.util.retry.Retry`; never `verify=False`. See skill `external-http-requests`.
- **stripe**: see skill `stripe-integration`. Never log secrets or full payloads containing card data.
- **sqlparse / tzdata / typing_extensions / certifi / idna / charset-normalizer / urllib3**: transitive or platform support; do not import directly unless needed.
