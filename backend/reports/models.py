from datetime import UTC, datetime, timedelta

from django.conf import settings
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

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
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf"],
                message="Только PDF файлы разрешены.",
            ),
        ],
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


class ReportSchedule(models.Model):
    """
    Расписание автоматической генерации отчётов.

    Позволяет настроить регулярную генерацию отчётов
    для организации с заданной частотой.
    """

    class Frequency(models.TextChoices):
        """Частота генерации отчётов."""

        DAILY = "daily", "Ежедневно"
        WEEKLY = "weekly", "Еженедельно"
        MONTHLY = "monthly", "Ежемесячно"

    # Организация
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="report_schedules",
        verbose_name="Организация",
    )

    # Тип отчёта
    report_type = models.CharField(
        max_length=20,
        choices=Report.ReportType.choices,
        verbose_name="Тип отчёта",
    )

    # Частота генерации
    frequency = models.CharField(
        max_length=20,
        choices=Frequency.choices,
        default=Frequency.MONTHLY,
        verbose_name="Частота генерации",
    )

    # Время запуска (часы:минуты в UTC)
    run_at_hour = models.PositiveIntegerField(
        default=9,
        validators=[MinValueValidator(0), MaxValueValidator(23)],
        verbose_name="Час запуска (UTC)",
        help_text="Час дня в UTC (0-23)",
    )
    run_at_minute = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(59)],
        verbose_name="Минута запуска (UTC)",
        help_text="Минута часа (0-59)",
    )

    # День недели для weekly (0=Понедельник, 6=Воскресенье)
    run_day_of_week = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        verbose_name="День недели (для weekly)",
        help_text="0=Пн, 1=Вт, ..., 6=Вс",
    )

    # День месяца для monthly (1-28, чтобы избежать проблем с короткими месяцами)
    run_day_of_month = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(28)],
        verbose_name="День месяца (для monthly)",
        help_text="День месяца (1-28)",
    )

    # Активность
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активно",
    )

    # Timestamps последнего и следующего запуска
    last_run_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Последний запуск",
    )
    next_run_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Следующий запуск",
    )

    # Создатель
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_schedules",
        verbose_name="Создал",
    )

    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создано",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Обновлено",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Расписание отчётов"
        verbose_name_plural = "Расписания отчётов"
        indexes = [
            models.Index(fields=["is_active", "next_run_at"]),
            models.Index(fields=["organization", "frequency"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "report_type", "frequency"],
                name="unique_schedule_per_org_report_frequency",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.organization.name} - {self.get_report_type_display()} "
            f"({self.get_frequency_display()})"
        )

    def calculate_next_run(self) -> datetime:
        """
        Рассчитывает время следующего запуска.

        Returns:
            datetime: Время следующего запуска в UTC.
        """
        now = timezone.now()

        if self.frequency == self.Frequency.DAILY:
            # Следующий день в указанное время
            next_run = now.replace(
                hour=self.run_at_hour,
                minute=self.run_at_minute,
                second=0,
                microsecond=0,
            )
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run

        if self.frequency == self.Frequency.WEEKLY:
            # Следующий указанный день недели
            days_ahead = self.run_day_of_week - now.weekday()
            if days_ahead < 0:
                days_ahead += 7

            next_run = (now + timedelta(days=days_ahead)).replace(
                hour=self.run_at_hour,
                minute=self.run_at_minute,
                second=0,
                microsecond=0,
            )
            if next_run <= now:
                next_run += timedelta(weeks=1)
            return next_run

        if self.frequency == self.Frequency.MONTHLY:
            # Следующий указанный день месяца
            target_year = now.year
            target_month = now.month

            # Пробуем текущий месяц
            try:
                next_run = now.replace(
                    day=self.run_day_of_month,
                    hour=self.run_at_hour,
                    minute=self.run_at_minute,
                    second=0,
                    microsecond=0,
                )
            except ValueError:
                # День не существует в этом месяце (например, 31 февраля)
                next_run = None

            if next_run is None or next_run <= now:
                # Переходим к следующему месяцу
                if target_month == 12:
                    target_year += 1
                    target_month = 1
                else:
                    target_month += 1

                try:
                    next_run = datetime(
                        year=target_year,
                        month=target_month,
                        day=self.run_day_of_month,
                        hour=self.run_at_hour,
                        minute=self.run_at_minute,
                        tzinfo=UTC,
                    )
                except ValueError:
                    # Если день не существует, берём последний день месяца
                    import calendar

                    _, last_day = calendar.monthrange(target_year, target_month)
                    next_run = datetime(
                        year=target_year,
                        month=target_month,
                        day=last_day,
                        hour=self.run_at_hour,
                        minute=self.run_at_minute,
                        tzinfo=UTC,
                    )

            return next_run

        # Fallback
        return now + timedelta(days=1)

    def save(self, *args, **kwargs):
        """
        При сохранении пересчитывает next_run_at, только если он не задан.

        Это позволяет явно устанавливать next_run_at в тестах и при
        программном создании расписаний.
        """
        if not self.next_run_at:
            self.next_run_at = self.calculate_next_run()
        super().save(*args, **kwargs)
