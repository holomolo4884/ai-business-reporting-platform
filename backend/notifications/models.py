from django.conf import settings
from django.db import models


class NotificationLog(models.Model):
    """
    Лог отправленных уведомлений.

    Хранит информацию о каждой попытке отправки уведомления:
    канал, получатель, статус, ошибки и связанные объекты.
    """

    class Status(models.TextChoices):
        """Статус уведомления."""

        PENDING = "pending", "В очереди"
        SUCCESS = "success", "Отправлено успешно"
        FAILED = "failed", "Ошибка отправки"
        RETRYING = "retrying", "Повторная попытка"

    class Channel(models.TextChoices):
        """Канал доставки."""

        EMAIL = "email", "Email"
        TELEGRAM = "telegram", "Telegram"
        WEBHOOK = "webhook", "Webhook"

    # Канал доставки
    channel = models.CharField(
        max_length=20,
        choices=Channel.choices,
        verbose_name="Канал доставки",
    )

    # Получатель (email / chat_id / URL)
    recipient = models.CharField(
        max_length=500,
        verbose_name="Получатель",
    )

    # Тема (для email)
    subject = models.CharField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="Тема",
    )

    # Сообщение
    message = models.TextField(
        verbose_name="Сообщение",
    )

    # Статус
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Статус",
    )

    # Детали ошибки (если есть)
    error_details = models.TextField(
        blank=True,
        default="",
        verbose_name="Детали ошибки",
    )

    # ID уведомления из notification-service
    notification_id = models.CharField(
        max_length=100,
        blank=True,
        default="",
        verbose_name="ID уведомления",
    )

    # Количество попыток отправки
    attempts = models.PositiveIntegerField(
        default=0,
        verbose_name="Количество попыток",
    )

    # Связанные объекты (опционально)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_logs",
        verbose_name="Пользователь",
    )

    report = models.ForeignKey(
        "reports.Report",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_logs",
        verbose_name="Отчёт",
    )

    # Дополнительные метаданные
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Метаданные",
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создано",
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Отправлено",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Notification Log"
        verbose_name_plural = "Notifications Logs"
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["report", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Notification {self.id} ({self.channel} to {self.recipient})"
