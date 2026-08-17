from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


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

    channel: NotificationChannel = Field(
        ...,
        description="Канал доставки",
    )
    recipient: str = Field(
        ...,
        description="Получатель (email/chat_id/URL)",
        min_length=1,
    )
    subject: str = Field(
        default="",
        description="Тема (для email)",
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
        description="Приоритет",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Дополнительные метаданные",
    )


class NotificationResponse(BaseModel):
    """Ответ от notification-service."""

    success: bool = Field(..., description="Успешно ли отправлено")
    message: str = Field(..., description="Сообщение о результате")
    notification_id: str | None = Field(
        default=None,
        description="ID уведомления",
    )
    error_details: str | None = Field(
        default=None,
        description="Детали ошибки",
    )
