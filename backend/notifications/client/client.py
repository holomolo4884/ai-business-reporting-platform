import logging
from typing import Any

import httpx
from django.conf import settings

from notifications.client.exceptions import (
    NotificationAuthenticationError,
    NotificationSendError,
    NotificationServiceUnavailableError,
    NotificationValidationError,
)
from notifications.client.schemas import (
    NotificationChannel,
    NotificationPriority,
    NotificationRequest,
    NotificationResponse,
)

logger = logging.getLogger(__name__)


class NotificationClient:
    """
    HTTP клиент для вызова notification-service.

    Использует X-API-Key заголовок для аутентификации.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int | None = None,
    ):
        self.base_url = (base_url or settings.NOTIFICATION_SERVICE_URL).rstrip("/")
        self.api_key = api_key or settings.NOTIFICATION_INTERNAL_API_KEY
        self.timeout = timeout or settings.NOTIFICATION_TIMEOUT_SECONDS

    def send_notification(
        self,
        channel: NotificationChannel | str,
        recipient: str,
        message: str,
        subject: str = "",
        priority: NotificationPriority | str = NotificationPriority.NORMAL,
        metadata: dict[str, Any] | None = None,
    ) -> NotificationResponse:
        """
        Отправляет уведомление через notification-service.

        Args:
            channel: Канал доставки (email/telegram/webhook).
            recipient: Получатель (email/chat_id/URL).
            message: Текст уведомления.
            subject: Тема (для email).
            priority: Приоритет (low/normal/high).
            metadata: Дополнительные метаданные.

        Returns:
            Ответ от notification-service.

        Raises:
            NotificationError: При ошибке отправки.
        """
        request = NotificationRequest(
            channel=NotificationChannel(channel),
            recipient=recipient,
            subject=subject,
            message=message,
            priority=NotificationPriority(priority),
            metadata=metadata,
        )

        url = f"{self.base_url}/api/v1/notifications/send/"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

        logger.info(
            "Отправка уведомления через notification-service: channel=%s, recipient=%s, url=%s",
            request.channel,
            request.recipient[:50],
            url,
        )

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    url,
                    json=request.model_dump(),
                    headers=headers,
                )

        except httpx.ConnectError as exc:
            logger.error(
                "Не удалось подключиться к notification-service: url=%s, error=%s",
                url,
                exc,
            )
            raise NotificationServiceUnavailableError(
                f"Notification-service недоступен по адресу {url}: {exc}"
            ) from exc

        except httpx.TimeoutException as exc:
            logger.error(
                "Таймаут при запросе к notification-service: url=%s, timeout=%ss",
                url,
                self.timeout,
            )
            raise NotificationServiceUnavailableError(
                f"Таймаут запроса к notification-service ({self.timeout}s)"
            ) from exc

        except httpx.RequestError as exc:
            logger.exception("Ошибка HTTP запроса к notification-service")
            raise NotificationServiceUnavailableError(
                f"Ошибка запроса к notification-service: {exc}"
            ) from exc

        # Обрабатываем ответ
        return self._process_response(response)

    def _process_response(self, response: httpx.Response) -> NotificationResponse:
        """Обрабатывает HTTP ответ от notification-service."""
        if response.status_code == 401:
            raise NotificationAuthenticationError("Неверный или отсутствует API ключ")

        if response.status_code == 403:
            raise NotificationAuthenticationError("Доступ запрещён (неверный API ключ)")

        if response.status_code == 422:
            error_details = response.text
            raise NotificationValidationError(f"Ошибка валидации данных: {error_details}")

        if response.status_code >= 500:
            raise NotificationServiceUnavailableError(
                f"Notification-service вернул HTTP {response.status_code}"
            )

        if response.status_code >= 400:
            raise NotificationSendError(
                f"Notification-service вернул HTTP {response.status_code}: {response.text}"
            )

        try:
            data = response.json()
            return NotificationResponse.model_validate(data)
        except Exception as exc:
            raise NotificationSendError(f"Не удалось распарсить ответ: {response.text}") from exc

    def is_healthy(self) -> bool:
        """
        Проверяет доступность notification-service.

        Returns:
            True если сервис здоров, False иначе.
        """
        url = f"{self.base_url}/api/v1/health/"
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url)
                return response.status_code == 200
        except Exception as exc:
            logger.warning(
                "Health check notification-service не удался: %s",
                exc,
            )
            return False


# Удобный alias
NotificationClientType = NotificationClient
