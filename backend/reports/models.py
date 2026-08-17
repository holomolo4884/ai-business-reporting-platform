from django.conf import settings
from django.db import models

from organizations.models import Organization


class Report(models.Model):
    """Модель отчёта."""

    class ReportType(models.TextChoices):
        SALES = "sales", "Sales Report"
        FINANCE = "finance", "Finance Report"
        CUSTOM = "custom", "Custom Report"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COLLECTING_DATA = "collecting_data", "Collecting Data"
        CALLING_AI = "calling_ai", "Calling AI"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    # Связи
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="reports",
        verbose_name="Organization",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_reports",
        verbose_name="Created by",
    )

    # Тип и статус
    report_type = models.CharField(
        max_length=20,
        choices=ReportType.choices,
        default=ReportType.SALES,
        verbose_name="Report type",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Status",
    )

    # Период отчёта
    period_start = models.DateTimeField(
        verbose_name="Period start",
    )
    period_end = models.DateTimeField(
        verbose_name="Period end",
    )

    # Данные отчёта
    metrics = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Collected metrics",
        help_text="Собранные бизнес-метрики в формате JSON",
    )
    ai_response = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="AI response",
        help_text="Ответ от AI в формате JSON",
    )
    generated_text = models.TextField(
        blank=True,
        verbose_name="Generated text",
        help_text="Сгенерированный текст отчёта",
    )
    generated_html = models.TextField(
        blank=True,
        verbose_name="Generated HTML",
        help_text="HTML версия отчёта",
    )
    error = models.TextField(
        blank=True,
        verbose_name="Error",
        help_text="Текст ошибки, если генерация не удалась",
    )

    # Файл отчёта
    pdf_file = models.FileField(
        upload_to="reports/pdf/%Y/%m/",
        null=True,
        blank=True,
        verbose_name="PDF file",
    )

    # Временные метки
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created at",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated at",
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Completed at",
    )

    class Meta:
        verbose_name = "report"
        verbose_name_plural = "reports"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "report_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Report #{self.id} - {self.report_type} ({self.status})"

    @property
    def is_completed(self) -> bool:
        return self.status == self.Status.COMPLETED

    @property
    def is_failed(self) -> bool:
        return self.status == self.Status.FAILED

    @property
    def is_in_progress(self) -> bool:
        return self.status in (
            self.Status.PENDING,
            self.Status.COLLECTING_DATA,
            self.Status.CALLING_AI,
        )

    @property
    def period_days(self) -> int:
        """Количество дней в периоде отчёта."""
        delta = self.period_end - self.period_start
        return delta.days
