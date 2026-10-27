---
name: django-background-tasks
description: Background work without Celery using Django 6 django.tasks, management commands and cron; idempotency and on_commit. Load for async/background jobs.
---
# Background Work (no Celery)

Django 6.0 introduced a tasks framework (`django.tasks`) defining the API (`@task`, `.enqueue()`), but **you must configure a backend** that actually runs tasks; built-in backends are for dev/test (immediate / dummy). Check the installed Django docs (`TASKS` setting) and choose deliberately.

```python
# orders/tasks.py
from django.tasks import task

@task()
def send_order_confirmation(order_id: int) -> None:
    order = Order.objects.select_related("user").get(pk=order_id)
    ...
```
Enqueue after commit:
```python
transaction.on_commit(lambda: send_order_confirmation.enqueue(order_id=order.pk))
```

## Options when no production task worker exists
| Need | Approach |
|---|---|
| Periodic jobs | Management command + platform cron/scheduler |
| Small deferred work | `on_commit` + synchronous short work |
| Reliable queue | DB-backed outbox table processed by a management command loop using `select_for_update(skip_locked=True)` |
| Heavy/scale | Ask the user before adding a broker/worker dependency |

## Rules
- Tasks take primitive args (IDs), are idempotent, re-fetch state, and handle "already done".
- Never pass model instances. Never enqueue inside uncommitted transactions.
- Log start/finish/failure. Retries with backoff and cap; poison messages go to a failed status.
- Stripe webhook processing: record event first, process quickly, return 2xx.
