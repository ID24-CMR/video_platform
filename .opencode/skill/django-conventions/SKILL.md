---
name: django-conventions
description: Idiomatic Django 6.1 project conventions: services/selectors, custom user, models, managers, views, URLs, admin. Load when creating apps, models or views.
---
# Django Conventions

## Custom user from day one
```python
# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    stripe_customer_id = models.CharField(max_length=64, blank=True, db_index=True)
```
`AUTH_USER_MODEL = "accounts.User"` must be set before the first `migrate`.

## Abstract base
```python
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True
```

## Custom QuerySet
```python
class OrderQuerySet(models.QuerySet):
    def paid(self): return self.filter(status=Order.Status.PAID)
    def for_user(self, user): return self.filter(user=user)

class Order(TimeStampedModel):
    objects = OrderQuerySet.as_manager()
```

## Services (writes) and selectors (reads)
```python
# orders/services.py
@transaction.atomic
def create_order(*, user: User, items: list[ItemInput]) -> Order:
    order = Order.objects.create(user=user, total_cents=sum(i.cents * i.qty for i in items))
    OrderLine.objects.bulk_create([OrderLine(order=order, ...) for i in items])
    transaction.on_commit(lambda: send_order_confirmation.enqueue(order_id=order.pk))
    return order

# orders/selectors.py
def orders_for_user(user: User) -> QuerySet[Order]:
    return Order.objects.for_user(user).select_related("user").prefetch_related("lines")
```
Keyword-only arguments for services. Services raise domain exceptions; views translate them to messages/status codes.

## Views
- Prefer class-based views for CRUD (`ListView`, `DetailView`, `FormView`), function views for simple endpoints.
- Use `LoginRequiredMixin` / `PermissionRequiredMixin`; override `get_queryset` to scope to `request.user`.
- Use `get_object_or_404(selector(...), pk=pk)`.
- POST-redirect-GET; `messages` framework for feedback.
- Health check at `/healthz/` returning `JsonResponse({"status": "ok"})` and verifying DB with `connection.ensure_connection()`.

## URLs
`app_name` in every `urls.py`; names like `orders:detail`; never hardcode URLs.

## Admin
`list_display`, `list_select_related`, `search_fields`, `list_filter`, `readonly_fields` for Stripe IDs and timestamps, `raw_id_fields` for big FKs, no heavy queries in `__str__`.

## Signals
Avoid for business logic. Allowed: decoupled cross-app notifications, registered in `AppConfig.ready()`.

## Django 6.x features to prefer
- Template partials (`{% partialdef %}` / `{% partial %}`) for reusable fragments.
- Built-in CSP support (`ContentSecurityPolicyMiddleware`, `SECURE_CSP`); verify exact setting names in the installed version.
- `django.tasks` framework for background work.
- `db_default`, `GeneratedField`, `CheckConstraint(condition=...)`, enum classes in `choices=`.
