from django.db import models


class Organization(models.Model):
    """Модель организации."""

    name = models.CharField(
        max_length=255,
        verbose_name="Organization name",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description",
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
        verbose_name = "organization"
        verbose_name_plural = "organizations"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
