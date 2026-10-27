# AUDIT REPORT

**Date:** 2026-10-24  
**Commit:** 1b8047769c72df142095af6be0016fe21d21aeeb  
**Scope:** Entire repository (videos app + config)

## 1) Executive summary

Single-app Django project. Focuses on video streaming with free/paid access and Stripe Checkout. 

| Area | Score /10 | Notes |
|---|---|---|
| Architecture | 4 | Single app, no services/selectors split, business logic in views. |
| Data/ORM | 5 | Good use of Decimal, unique constraints, select_related; missing pagination/indexes. |
| Security | 3 | ALLOWED_HOSTS=["*"], insecure SECRET_KEY fallback, csrf_exempt webhook needs care. |
| Payments | 5 | Good idempotency (ProcessedStripeEvent), amount verification, atomic webhook. Some gaps. |
| Migrations | 6 | 4 migrations, appear clean schema. |
| Tests | 1 | Only `videos/tests.py` empty/default. |
| Performance | 4 | Some select_related, but unbounded querysets, no pagination. |
| Deploy | 2 | Missing production hardening, .env.example incomplete. |
| Dependencies | 3 | requirements.txt missing stripe/dj-database-url/psycopg2/whitenoise; env has different versions. |

**Go/No-go for production: NO-GO.** Multiple critical security issues and missing tests/deploy controls.

## 2) Automated check results

| Check | Result | Notes |
|---|---|---|
| `python manage.py check` | NOT VERIFIED | ModuleNotFoundError: dj_database_url (not installed) |
| `DJANGO_SETTINGS_MODULE=config.settings.production ... check --deploy` | NOT VERIFIED | No production settings module found; dj_database_url missing |
| `python manage.py makemigrations --check --dry-run` | NOT VERIFIED | deps missing |
| `python manage.py showmigrations --plan \| grep "\[ \]"` | NOT VERIFIED | deps/DB missing |
| `ruff check . --statistics` and `ruff format --check .` | NOT VERIFIED | ruff not installed |
| `mypy .` | NOT VERIFIED | no config |
| `pytest -q ...` | NOT VERIFIED | deps missing |
| `pip check` and `pip list --outdated` | FAIL/NOT VERIFIED | Django 5.1.4 installed vs 6.1 req; missing stripe, dj-database-url, psycopg2-binary, whitenoise in env |
| `python -W error::DeprecationWarning manage.py check` | NOT VERIFIED | deps missing |
| Secret scan (manual grep patterns) | NOT VERIFIED | grep unavailable in shell; manual review shows no live keys committed |

## 3) Findings

| ID | Severity | Area | file:line | Problem | Impact | Recommended fix | Effort |
|---|---|---|---|---|---|---|---|
| F001 | Critical | Security | config/settings.py:46 | `ALLOWED_HOSTS = ["*"]` | Host header attacks, cache poisoning | Use env-driven list; require explicit hosts in prod | S |
| F002 | Critical | Security | config/settings.py:28-29 | Insecure `SECRET_KEY` fallback `"django-insecure-local-development-only"` | Token forgery | Require `DJANGO_SECRET_KEY` from env; fail fast if missing in prod | S |
| F003 | High | Security | config/settings.py:95-108 | DEBUG defaults via env; defaults False but combined with F001 dangerous | Info disclosure | Enforce secure defaults, add `check --deploy` | S |
| F004 | High | Security | videos/views.py:456-545 | `@csrf_exempt` on webhook; relies on signature verification | CSRF not relevant but surface area | Ensure signature check before processing; rate limit; consider raw body only | S |
| F005 | High | AuthZ | videos/views.py:43-54, 80+ | Admin views use `@user_passes_test(is_main_admin)` checking `is_superuser` only | Privilege escalation if superuser assigned broadly | Role-based perms, `@staff_member_required` or custom perms; audit trail | M |
| F006 | High | Auth | All views | No custom user model; uses default auth.User | Migration pain later | Create `accounts` app with custom user before more FKs | L |
| F007 | Medium | ORM/Perf | videos/views.py:175-232 | `manage_videos` unbounded queryset, filters via GET, no pagination | DoS/slow queries | Paginate with `Paginator`, add indexes | M |
| F008 | Medium | ORM/Perf | videos/views.py:300-324 | `public_video_library` unbounded, search with `icontains` | Perf | Paginate, consider trigram/GIN if large | M |
| F009 | Medium | Models | videos/models.py:96-140 | `VideoAccessGrant.on_delete=models.CASCADE` | Losing audit trail of grants on video deletion | Use `PROTECT` or soft-delete | S |
| F010 | Medium | Models | videos/models.py:58-94 | `Video.clean()` validates price rules; DB has no CheckConstraint for money rules | Inconsistent data possible outside forms/admin | Add `CheckConstraint` (Django 6 supports `condition=`) | M |
| F011 | Medium | Payments | videos/views.py:363-453 | `amount_in_cents = int((video.price*Decimal("100")).quantize(Decimal("1")))` | Rounding; better use integer arithmetic | `int(video.price * 100)` after validation or `quantize` with ROUND_DOWN/ensure integer cents | S |
| F012 | Medium | Security/Files | videos/storage.py, models.py:77-90 | Private video storage used; no validation on upload size/type for Video.video_file/thumbnail | Abuse | Validate in form/model, restrict extensions, size limits | M |
| F013 | Low | Views | videos/views.py:358-361 | Redirect if `STRIPE_SECRET_KEY` missing shows message | Config error | Better logging/alerting | S |
| F014 | Low | Code quality | videos/views.py:1-40 | Many imports duplicated/redundant | Noise | Clean imports | S |
| F015 | Info | Deps | requirements.txt | Missing stripe, dj-database-url, psycopg2-binary, whitenoise; has different packages | Mismatch vs settings | Align requirements to match settings/code | M |

## 4) Top 10 priorities (fix order)

1. **F001 ALLOWED_HOSTS** - Prevent host header attacks (S)  
2. **F002 SECRET_KEY** - Remove insecure fallback (S)  
3. **F015 Dependencies** - Install/align deps (M)  
4. **F007/F008 Pagination** - Prevent unbounded queries (M)  
5. **F005 Admin authZ** - Strengthen permissions (M)  
6. **F006 Custom user model** - Plan migration path (L)  
7. **F009/F010 Model constraints** - Data integrity (M)  
8. **F004/F payments webhook hardening** - Review edge cases (S)  
9. **F012 Upload validation** - Prevent abuse (M)  
10. **Tests (empty)** - Add critical tests (L)

## 5) Quick wins (< 30 min)

- Set `ALLOWED_HOSTS` from env with safe default
- Require `SECRET_KEY` from env (no fallback)
- Add pagination to list views
- Add `CheckConstraint` for price rules
- Change `VideoAccessGrant.on_delete` to `PROTECT`

## 6) Migration & data risks

Migrations 0001-0004 look standard. `ProcessedStripeEvent` added for idempotency. Changing `on_delete` requires migration. Adding constraints may need data cleanup. No data migrations mixing with schema changes observed. Reversibility appears okay.

## 7) Test gaps

`videos/tests.py` is empty. Need: permission matrix (anon/auth/superuser), free/paid access control, purchase flow, webhook idempotency (duplicate events), amount/currency mismatch, pagination, search filters, query count tests (`django_assert_num_queries`).

## 8) What is done well

- Uses `Decimal` for money (models.py:66-90, views.py:402-453)
- Webhook verifies signature, uses `transaction.atomic()`, `select_for_update()`, idempotency table, metadata validation, amount/currency checks
- `select_related` used in places
- Unique constraints present
- Private file storage for videos
- Open redirect protection via `url_has_allowed_host_and_scheme`

## 9) Remediation roadmap

**Week 1:** Security fixes (F001,F002), align deps, add pagination, basic constraints. Commands: `/check-deploy`, `/test`  
**Week 2:** AuthZ hardening, upload validation, model constraints, start tests.  
**Later:** Custom user model migration plan, performance tuning, full test coverage.

## 10) Appendix

**Commands run:** `git log/rev-parse/ls-files`, attempted `manage.py check` (failed due deps).  
**Versions (env):** Django 5.1.4, Python 3.12.  
**Files reviewed:** config/settings.py, config/urls.py, videos/{models,views,urls,forms,admin,storage,migrations/*,tests.py}, templates, static.  
**Not verified:** DB checks, ruff/pytest/mypy (missing tools/deps).
