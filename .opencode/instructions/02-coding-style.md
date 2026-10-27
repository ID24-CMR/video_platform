# Coding Style

- Python 3.12+ (required by Django 6.x). Type hints on all service/selector functions; docstrings only where intent is not obvious.
- Formatter/linter: **ruff** (`ruff format`, `ruff check`). Line length 100. Imports sorted by ruff (isort rules).
- Naming: `snake_case` functions/modules, `PascalCase` classes, `UPPER_SNAKE` constants. Model names singular. `related_name` always explicit and plural for reverse FK sets.
- Prefer `pathlib.Path` over `os.path`. Prefer f-strings. Never `print()`, use `logging.getLogger(__name__)`.
- Never catch bare `Exception` and swallow it. Catch specific exceptions; use `logger.exception` when logging unexpected errors.
- `Model.objects.get()` must handle `DoesNotExist` / `MultipleObjectsReturned`, or use `get_object_or_404` in views.
- No mutable default args. No wildcard imports. No unused imports.
- Use `TextChoices` / `IntegerChoices` for enums.
- Use `settings.AUTH_USER_MODEL` in model FKs and `get_user_model()` at runtime.
- Use `from __future__ import annotations` only when it solves a real forward-reference problem.
- Show file path as header above each code block when presenting code (`# billing/services.py`).

## Model conventions

```python
class Order(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=20, choices=Status, default=Status.PENDING, db_index=True)
    total_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="eur")

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(total_cents__gte=0), name="order_total_non_negative"),
        ]
        indexes = [models.Index(fields=["user", "-created_at"])]
```

Note: Django 6 `CheckConstraint` uses the `condition=` keyword (the old `check=` was removed). `choices=` accepts the enum class directly.

## Templates

- Template inheritance from `templates/base.html`. Escape by default; never `mark_safe` user input.
- Use `{% url %}`, `{% static %}`. No business logic in templates; use properties or template tags sparingly.
