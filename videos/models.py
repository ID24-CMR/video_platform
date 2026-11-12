
from decimal import Decimal

from django.core.exceptions import ValidationError
from .storage import private_video_storage
from django.db import models
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Video(models.Model):
    class AccessType(models.TextChoices):
        FREE = "free", "Free"
        PAID = "paid", "Paid"

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="videos",
    )

    video_file = models.FileField(
    upload_to="videos/",
    storage=private_video_storage
)
    thumbnail = models.ImageField(
        upload_to="thumbnails/",
        blank=True,
    )

    access_type = models.CharField(
        max_length=10,
        choices=AccessType.choices,
        default=AccessType.FREE,
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        super().clean()

        if self.price < Decimal("0.00"):
            raise ValidationError({
                "price": "The price cannot be negative."
            })

        if (
            self.access_type == self.AccessType.FREE
            and self.price != Decimal("0.00")
        ):
            raise ValidationError({
                "price": "Free videos must have a price of 0."
            })

        if (
            self.access_type == self.AccessType.PAID
            and self.price <= Decimal("0.00")
        ):
            raise ValidationError({
                "price": "Paid videos must have a price greater than 0."
            })

    def __str__(self):
        return self.title

class VideoAccessGrant(models.Model):
    class GrantSource(models.TextChoices):
        MANUAL = "manual", "Manual"
        PAYMENT = "payment", "Payment"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="video_access_grants"
    )

    video = models.ForeignKey(
        Video,
        on_delete=models.PROTECT,
        related_name="access_grants"
    )

    source = models.CharField(
        max_length=10,
        choices=GrantSource.choices,
        default=GrantSource.MANUAL
    )

    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "video"],
                name="unique_user_video_access"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.video.title}"

class Purchase(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        CANCELED = "canceled", "Canceled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="video_purchases"
    )

    video = models.ForeignKey(
        Video,
        on_delete=models.PROTECT,
        related_name="purchases"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    currency = models.CharField(
        max_length=3,
        default="cad"
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )

    stripe_checkout_session_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )

    stripe_payment_intent_id = models.CharField(
        max_length=255,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return (
            f"Purchase #{self.pk} - "
            f"{self.user.username} - {self.video.title}"
        )
    
# A webhook event model

# Stripe may deliver the same event more than once.
# Your application must avoid granting access repeatedly or processing a payment twice.

class ProcessedStripeEvent(models.Model):
    event_id = models.CharField(
        max_length=255,
        unique=True
    )

    event_type = models.CharField(max_length=100)

    processed_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.event_id