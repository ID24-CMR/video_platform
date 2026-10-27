---
name: django-orm-performance
description: Django ORM query performance, N+1 avoidance, indexes, transactions, bulk operations and concurrency on PostgreSQL. Load for slow queries or data-heavy features.
---
# ORM and Performance

## Always think in query counts
- FK / OneToOne: `select_related("author")`.
- Reverse FK / M2M: `prefetch_related("lines")`; filtered: `Prefetch("lines", queryset=Line.objects.filter(active=True), to_attr="active_lines")`.
- Wide tables: `.only()`, `.defer()`, `.values()`, `.values_list(flat=True)`.
- `.exists()` not truthiness; `.count()` not `len(qs)`; `.iterator(chunk_size=2000)` for big scans.

## Push work to the DB
```python
from django.db.models import Count, Sum, F, Q, Exists, OuterRef, Subquery, Case, When

Order.objects.annotate(line_count=Count("lines"), paid_total=Sum("lines__cents", filter=Q(status="paid")))
Product.objects.filter(Exists(OrderLine.objects.filter(product=OuterRef("pk"))))
Counter.objects.filter(pk=pk).update(hits=F("hits") + 1)     # atomic counter
```

## Indexes
- Index columns used in `filter`, `order_by`, joins. Composite index order = equality columns first, then range/sort.
- Partial index: `Index(fields=["created_at"], condition=Q(status="pending"), name="order_pending_idx")`.
- Check with `qs.explain(analyze=True)`; avoid indexes on low-cardinality columns alone.
- On large live tables use `AddIndexConcurrently` (`django.contrib.postgres.operations`) in a non-atomic migration.

## Transactions and concurrency
```python
with transaction.atomic():
    acct = Account.objects.select_for_update().get(pk=pk)    # lock row
    acct.balance_cents -= amount
    acct.save(update_fields=["balance_cents"])
transaction.on_commit(lambda: notify.enqueue(account_id=pk))   # side effects after commit
```
- `select_for_update(skip_locked=True)` for work queues.
- Use `get_or_create` / `update_or_create` only with a unique constraint backing them.
- `bulk_create(..., batch_size=1000)`, `bulk_update(..., fields=[...])`; remember they skip `save()` and signals.
- Keep transactions short; no HTTP calls to Stripe/requests inside a DB transaction holding locks.

## Connections
`CONN_MAX_AGE=60`, `CONN_HEALTH_CHECKS=True` with gunicorn sync workers. Avoid per-request connection churn.

## Testing
```python
def test_list_queries(client, django_assert_num_queries, order_factory):
    order_factory.create_batch(10)
    with django_assert_num_queries(3):
        client.get(reverse("orders:list"))
```

## Pagination
`Paginator` / `ListView.paginate_by`; for huge tables use keyset pagination (`filter(id__lt=cursor)[:n]`), avoid deep `OFFSET`.

## Caching
Start with per-view or low-level cache on measured hot paths; use `cache.get_or_set`, explicit invalidation, never cache per-user data under a shared key.
