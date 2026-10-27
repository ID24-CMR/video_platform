---
description: Add a verified, idempotent Stripe webhook handler
agent: stripe-payments
---
Implement/extend the Stripe webhook for events: $ARGUMENTS

Deliver: `billing/models.py::StripeEvent` (unique `event_id`, `type`, `processed_at`, `payload` JSON optional), `billing/webhooks.py` handler registry, `billing/views.py::stripe_webhook` (`@csrf_exempt`, `@require_POST`, signature verification, returns 400 on bad signature/payload, 200 when handled or already processed), service functions for fulfillment in `transaction.atomic()`, URL, `.env.example` entries, and tests that post signed payloads (generate signature with `stripe.WebhookSignature`-compatible header or mock `construct_event`).
