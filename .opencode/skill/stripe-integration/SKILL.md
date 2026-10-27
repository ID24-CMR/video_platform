---
name: stripe-integration
description: Stripe (stripe==16.0.0) Checkout, webhooks, idempotency, subscriptions, refunds and testing in Django. Load for any payment work.
---
# Stripe Integration

> Verify method names/types against the installed SDK (`python -c "import stripe; print(stripe.__version__)"`) and Stripe docs before use. SDK major versions pin an API version; set it explicitly.

## Configuration
```python
# billing/stripe_client.py
import stripe
from django.conf import settings

def get_client() -> stripe.StripeClient:
    return stripe.StripeClient(settings.STRIPE_SECRET_KEY)   # client-based API; no global mutable key
```
(Alternative legacy style: `stripe.api_key = ...` once in `AppConfig.ready()`.)

## Models
```python
class StripeCustomer(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="stripe_customer")
    stripe_id = models.CharField(max_length=64, unique=True)

class Payment(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending"; PAID = "paid"; FAILED = "failed"; REFUNDED = "refunded"
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="payments")
    amount_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=16, choices=Status, default=Status.PENDING)
    stripe_session_id = models.CharField(max_length=128, unique=True, null=True, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=128, unique=True, null=True, blank=True)

class StripeEvent(models.Model):
    event_id = models.CharField(max_length=64, unique=True)
    type = models.CharField(max_length=100)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
```
Use `PROTECT` for financial data. Money in integer cents.

## Checkout session (server decides price)
```python
def create_checkout_session(*, user, price_id: str, quantity: int, payment: Payment) -> str:
    session = get_client().checkout.sessions.create(
        params={
            "mode": "payment",
            "line_items": [{"price": price_id, "quantity": quantity}],
            "success_url": f"{settings.SITE_URL}{reverse('billing:success')}?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{settings.SITE_URL}{reverse('billing:cancel')}",
            "client_reference_id": str(payment.pk),
            "metadata": {"payment_id": str(payment.pk), "user_id": str(user.pk)},
        },
        options={"idempotency_key": f"checkout-{payment.pk}"},
    )
    Payment.objects.filter(pk=payment.pk).update(stripe_session_id=session.id)
    return session.url
```
Do not call Stripe inside a transaction holding row locks. Never take amount/price from the browser.

## Webhook (authoritative source of truth)
```python
@csrf_exempt
@require_POST
def stripe_webhook(request):
    try:
        event = stripe.Webhook.construct_event(
            payload=request.body,
            sig_header=request.META.get("HTTP_STRIPE_SIGNATURE", ""),
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except (ValueError, stripe.SignatureVerificationError):
        return HttpResponse(status=400)

    obj, created = StripeEvent.objects.get_or_create(event_id=event["id"], defaults={"type": event["type"]})
    if not created and obj.processed_at:
        return HttpResponse(status=200)          # idempotent replay

    handler = HANDLERS.get(event["type"])
    if handler:
        with transaction.atomic():
            handler(event)
            StripeEvent.objects.filter(pk=obj.pk).update(processed_at=timezone.now())
    return HttpResponse(status=200)
```
Handle at least: `checkout.session.completed`, `checkout.session.async_payment_succeeded/failed`, `payment_intent.payment_failed`, `charge.refunded`; for subscriptions: `customer.subscription.created/updated/deleted`, `invoice.paid`, `invoice.payment_failed`. Handlers must tolerate out-of-order and duplicate events and fetch fresh object state from Stripe when needed. Return 2xx fast; heavy work in background tasks. Use `stripe listen --forward-to localhost:8000/billing/webhook/` for local dev.

## Customer portal & refunds
Billing portal session for self-service; refunds via `refunds.create` with idempotency key, update `Payment.status` from the `charge.refunded` webhook, not optimistically.

## Security
- Verify signature always; webhook URL has no auth other than signature.
- Never log `STRIPE_SECRET_KEY`, webhook secret, or full payloads with PII.
- Restrict API key permissions (restricted keys) in production.
- Separate test/live keys per environment; `.env.example` has placeholders only.

## Tests
- Mock Stripe SDK calls at the boundary.
- Webhook tests: compute a real signature with `stripe.WebhookSignature._compute_signature` equivalent or patch `construct_event`; test replay idempotency, bad signature (400), unknown event type (200), out-of-order events.
- Assert fulfillment happens exactly once.

## Go-live checklist
Live keys in env, webhook endpoint registered with correct events, HTTPS, `SITE_URL` correct, tax/invoice settings, receipts, dispute handling, monitoring of failed webhook deliveries.
