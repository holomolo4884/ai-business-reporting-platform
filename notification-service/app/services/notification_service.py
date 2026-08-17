import uuid

from structlog import get_logger

from app.schemas.notification import (
    NotificationChannel,
    NotificationRequest,
    NotificationResponse,
)
from app.services.base import BaseSender
from app.services.email_sender import EmailSender
from app.services.telegram_sender import TelegramSender
from app.services.webhook_sender import WebhookSender

logger = get_logger()


class NotificationService:
    """
    Главный сервис уведомлений.

    Роутит уведомления по каналам (email, telegram, webhook)
    и возвращает стандартизированный ответ.
    """

    def __init__(self):
        # Инициализируем отправителей для каждого канала
        self._senders: dict[NotificationChannel, BaseSender] = {
            NotificationChannel.EMAIL: EmailSender(),
            NotificationChannel.TELEGRAM: TelegramSender(),
            NotificationChannel.WEBHOOK: WebhookSender(),
        }

    async def send(self, request: NotificationRequest) -> NotificationResponse:
        """Отправляет уведомление через указанный канал."""
        notification_id = str(uuid.uuid4())

        logger.info(
            "Обработка запроса на уведомление",
            notification_id=notification_id,
            channel=request.channel,
            recipient=request.recipient[:50],
            priority=request.priority,
        )

        # Получаем отправитель для выбранного канала
        sender = self._senders.get(request.channel)
        if not sender:
            return NotificationResponse(
                success=False,
                message=f"Неизвестный канал: {request.channel}",
                notification_id=notification_id,
            )

        # Отправляем
        result = await sender.send(
            recipient=request.recipient,
            subject=request.subject,
            message=request.message,
            metadata=request.metadata,
        )

        logger.info(
            "Уведомление обработано",
            notification_id=notification_id,
            success=result.success,
        )

        return NotificationResponse(
            success=result.success,
            message=result.message,
            notification_id=notification_id,
            error_details=result.error_details,
        )


# Синглтон для использования во всём приложении
notification_service = NotificationService()
