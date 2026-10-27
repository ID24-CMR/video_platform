---
name: whitenoise-static-media
description: Serving static files with whitenoise 6.12 and handling media uploads safely in production. Load for static/media problems.
---
# Whitenoise and Media

## Setup
- Middleware right after `SecurityMiddleware`.
- `STORAGES["staticfiles"]["BACKEND"] = "whitenoise.storage.CompressedManifestStaticFilesStorage"` in production; plain `StaticFilesStorage` in tests/local.
- `STATIC_ROOT = BASE_DIR / "staticfiles"`; run `collectstatic --noinput` at build/release.
- Cache headers are automatic for hashed (manifest) files.

## Common problems
| Symptom | Cause / fix |
|---|---|
| `ValueError: Missing staticfiles manifest entry` | `collectstatic` not run, or template references missing file. Fix path or run collectstatic. In tests use non-manifest storage. |
| Admin unstyled in production | `collectstatic` missing or `STATIC_ROOT` mismatch |
| 404 on new static files | Whitenoise does not rescan in production; redeploy/collectstatic |
| Wrong compression | Do not double-compress with proxy for already `.gz`/`.br` files |

## Media files
Whitenoise **does not serve user-uploaded media** (it is for static assets). For production use object storage (S3-compatible via an approved storage backend) or a proxy serving a volume. In dev, add `static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)` to `urls.py` only when `DEBUG`.

## Optional
`WHITENOISE_MAX_AGE`, `WHITENOISE_KEEP_ONLY_HASHED_FILES`, `WHITENOISE_MANIFEST_STRICT` (check docs of installed version before using).
