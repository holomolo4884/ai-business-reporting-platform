from django.db import models

from organizations.models import Organization


class Order(models.Model):
    """Модель заказа."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"

    class Currency(models.TextChoices):
        USD = "USD", "US Dollar"
        EUR = "EUR", "Euro"
        RUB = "RUB", "Russian Ruble"
        GBP = "GBP", "British Pound"
        JPY = "JPY", "Japanese Yen"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Organization",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Amount",
    )
    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.USD,
        verbose_name="Currency",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Status",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description",
    )
    order_date = models.DateTimeField(
        verbose_name="Order date",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created at",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated at",
    )

    class Meta:
        verbose_name = "order"
        verbose_name_plural = "orders"
        ordering = ["-order_date"]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "order_date"]),
        ]

    def __str__(self):
        return f"Order #{self.id} - {self.amount} {self.currency} ({self.status})"

    @property
    def is_paid(self) -> bool:
        return self.status == self.Status.PAID

    @property
    def is_cancelled(self) -> bool:
        return self.status == self.Status.CANCELLED
