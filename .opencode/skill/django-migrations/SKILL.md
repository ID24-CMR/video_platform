---
name: django-migrations
description: Zero-downtime Django migrations on PostgreSQL, data migrations, large tables, squashing and conflict resolution. Load when changing models or reviewing migrations.
---
# Migrations and Schema

## Rules
1. Never edit an applied migration. Add a new one.
2. Name them: `makemigrations app --name add_order_status_index`.
3. Always inspect SQL: `python manage.py sqlmigrate app 0007`.
4. Separate schema migrations from data migrations.
5. Make deploys backward compatible: old code must run against the new schema during rollout.

## Safe vs risky operations (PostgreSQL)
| Change | Safety |
|---|---|
| Add nullable column | Safe |
| Add column with `db_default` / constant default | Usually safe on modern PostgreSQL (no rewrite) |
| Add NOT NULL column without default | Needs 3 steps |
| Drop column | Step 1 stop using it in code, step 2 drop later |
| Rename column/table | Risky; use add new, backfill, switch, drop old |
| Add index | Use `AddIndexConcurrently` (non-atomic migration) |
| Add FK / unique / check constraint | Add `NOT VALID` then `VALIDATE`; in Django use `RunSQL` or separate steps for large tables |
| Change column type | Often rewrites table; do new column + backfill |

## Non-atomic concurrent index
```python
from django.contrib.postgres.operations import AddIndexConcurrently
class Migration(migrations.Migration):
    atomic = False
    operations = [AddIndexConcurrently("order", models.Index(fields=["status", "-created_at"], name="order_status_created_idx"))]
```

## Data migration template
```python
def forwards(apps, schema_editor):
    Order = apps.get_model("orders", "Order")          # never import real models
    qs = Order.objects.filter(currency="")
    for batch_ids in batched(qs.values_list("pk", flat=True).iterator(), 5000):
        Order.objects.filter(pk__in=batch_ids).update(currency="eur")

migrations.RunPython(forwards, migrations.RunPython.noop)
```
Backfill in batches, outside long transactions on big tables (set `atomic = False` if necessary).

## 3-step NOT NULL
1. Add nullable column, deploy code writing both.
2. Backfill in batches.
3. Add NOT NULL (or check constraint) after verification.

## Conflicts and hygiene
- Merge conflicts: `python manage.py makemigrations --merge`.
- CI: `makemigrations --check --dry-run` must pass.
- Squash only when all environments applied the originals.
- `AUTH_USER_MODEL` swap only before first migration.
