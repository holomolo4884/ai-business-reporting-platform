import logging
from typing import Any

from notifications.client.client import NotificationClient
from notifications.client.exceptions import NotificationError
from notifications.client.schemas import NotificationChannel, NotificationPriority

logger = logging.getLogger(__name__)


def send_email(
    recipient: str,
    subject: str,
    message: str,
    priority: NotificationPriority | str = NotificationPriority.NORMAL,
    metadata: dict[str, Any] | None = None,
    raise_on_error: bool = False,
) -> bool:
    """
    Отправляет email уведомление.

    Returns:
        True если успешно, False при ошибке.

    Raises:
        NotificationError: Если raise_on_error=True.
    """
    try:
        client = NotificationClient()
        response = client.send_notification(
            channel=NotificationChannel.EMAIL,
            recipient=recipient,
            subject=subject,
            message=message,
            priority=priority,
            metadata=metadata,
        )
        return response.success
    except NotificationError:
        if raise_on_error:
            raise
        logger.exception("Ошибка при отправке email")
        return False


def send_telegram(
    chat_id: str,
    message: str,
    subject: str = "",
    priority: NotificationPriority | str = NotificationPriority.NORMAL,
    metadata: dict[str, Any] | None = None,
    raise_on_error: bool = False,
) -> bool:
    """
    Отправляет Telegram уведомление.

    Returns:
        True если успешно, False при ошибке.
    """
    try:
        client = NotificationClient()
        response = client.send_notification(
            channel=NotificationChannel.TELEGRAM,
            recipient=chat_id,
            subject=subject,
            message=message,
            priority=priority,
            metadata=metadata,
        )
        return response.success
    except NotificationError:
        if raise_on_error:
            raise
        logger.exception("Ошибка при отправке Telegram")
        return False


def send_webhook(
    url: str,
    message: str,
    subject: str = "",
    priority: NotificationPriority | str = NotificationPriority.NORMAL,
    metadata: dict[str, Any] | None = None,
    raise_on_error: bool = False,
) -> bool:
    """
    Отправляет webhook уведомление.

    Returns:
        True если успешно, False при ошибке.
    """
    try:
        client = NotificationClient()
        response = client.send_notification(
            channel=NotificationChannel.WEBHOOK,
            recipient=url,
            subject=subject,
            message=message,
            priority=priority,
            metadata=metadata,
        )
        return response.success
    except NotificationError:
        if raise_on_error:
            raise
        logger.exception("Ошибка при отправке webhook")
        return False
