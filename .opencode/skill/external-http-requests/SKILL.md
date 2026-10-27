---
name: external-http-requests
description: Calling external APIs with requests 2.34 safely: timeouts, retries, sessions, error handling, SSRF, testing. Load when integrating third-party HTTP APIs.
---
# Outbound HTTP with requests

```python
# core/http.py
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_TIMEOUT = (3.05, 10)   # connect, read

def build_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(total=3, backoff_factor=0.5, status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=frozenset({"GET", "HEAD", "OPTIONS"}))
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers.update({"User-Agent": "myapp/1.0"})
    return s
```

## Rules
1. **Always `timeout=`.** Never rely on default (infinite).
2. Retry only idempotent methods unless an idempotency key is used.
3. Never `verify=False`. certifi provides the CA bundle.
4. `response.raise_for_status()` inside try/except `requests.RequestException`; log with `logger.warning` including status and URL (no secrets); raise a domain exception (`ExternalServiceError`).
5. Parse JSON defensively (`response.json()` may raise `requests.JSONDecodeError`).
6. Do not call external services inside open DB transactions or in `save()`.
7. SSRF: if URL comes from a user, allowlist hosts, block private IP ranges, disable redirects (`allow_redirects=False`).
8. Slow integrations run in background tasks, not request cycle.
9. Wrap each integration in a client class in `<app>/clients.py`; inject for easy mocking.
10. Tests use `responses`; no real network.

Stripe uses its own SDK; do not hand-roll Stripe HTTP calls with `requests`.
