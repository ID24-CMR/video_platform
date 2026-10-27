---
description: Audit pinned dependencies for compatibility and known issues
agent: build
---
Audit `requirements.txt`:

!`pip list --outdated 2>/dev/null | head -50`

Check: compatibility matrix (Django 6.1 vs Python version, psycopg2 vs Postgres version), transitive pins (urllib3/requests/certifi/idna/charset-normalizer consistent), deprecation warnings (`python -W error::DeprecationWarning manage.py check`), and `pip check`. Do NOT change pins; propose changes with rationale and risk.
