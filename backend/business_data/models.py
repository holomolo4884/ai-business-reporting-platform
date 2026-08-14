from django.db import models

from organizations.models import Organization


class Currency(models.TextChoices):
    """Общее перечисление валют."""

    USD = "USD", "US Dollar"
    EUR = "EUR", "Euro"
    RUB = "RUB", "Russian Ruble"
    GBP = "GBP", "British Pound"
    JPY = "JPY", "Japanese Yen"


class Order(models.Model):
    """Модель заказа."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"

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


class Expense(models.Model):
    """Модель расхода."""

    class Category(models.TextChoices):
        RENT = "rent", "Rent"
        SALARY = "salary", "Salary"
        MARKETING = "marketing", "Marketing"
        UTILITIES = "utilities", "Utilities"
        EQUIPMENT = "equipment", "Equipment"
        SOFTWARE = "software", "Software"
        TRAVEL = "travel", "Travel"
        OTHER = "other", "Other"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="expenses",
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
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER,
        verbose_name="Category",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description",
    )
    expense_date = models.DateTimeField(
        verbose_name="Expense date",
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
        verbose_name = "expense"
        verbose_name_plural = "expenses"
        ordering = ["-expense_date"]
        indexes = [
            models.Index(fields=["organization", "category"]),
            models.Index(fields=["organization", "expense_date"]),
        ]

    def __str__(self):
        return f"Expense #{self.id} - {self.amount} {self.currency} ({self.category})"
