"""
Pydantic схемы для уведомлений.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NotificationChannel(str, Enum):
    """Каналы доставки уведомлений."""

    EMAIL = "email"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"


class NotificationPriority(str, Enum):
    """Приоритет уведомления."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class NotificationRequest(BaseModel):
    """Запрос на отправку уведомления."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "channel": "email",
                "recipient": "user@example.com",
                "subject": "Отчёт готов",
                "message": "Ваш отчёт успешно сгенерирован и доступен для скачивания.",
                "priority": "normal",
                "metadata": {"report_id": 42},
            }
        }
    )

    channel: NotificationChannel = Field(
        ...,
        description="Канал доставки уведомления",
    )
    recipient: str = Field(
        ...,
        description="Получатель (email, telegram chat_id, webhook URL)",
        min_length=1,
    )
    subject: str = Field(
        default="",
        description="Тема уведомления (для email)",
        max_length=500,
    )
    message: str = Field(
        ...,
        description="Текст уведомления",
        min_length=1,
        max_length=10000,
    )
    priority: NotificationPriority = Field(
        default=NotificationPriority.NORMAL,
        description="Приоритет уведомления",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Дополнительные метаданные",
    )


class NotificationResponse(BaseModel):
    """Ответ на запрос отправки уведомления."""

    success: bool = Field(..., description="Успешно ли отправлено")
    message: str = Field(..., description="Сообщение о результате")
    notification_id: str | None = Field(
        default=None,
        description="ID уведомления",
    )
    error_details: str | None = Field(
        default=None,
        description="Детали ошибки (если есть)",
    )


class HealthResponse(BaseModel):
    """Ответ health check endpoint'а."""

    status: str = Field(..., description="Статус сервиса")
    service: str = Field(..., description="Название сервиса")
    version: str = Field(default="1.0.0", description="Версия")
