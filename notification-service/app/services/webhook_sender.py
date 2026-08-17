import httpx
from structlog import get_logger

from app.services.base import BaseSender, SendResult

logger = get_logger()


class WebhookSender(BaseSender):
    """Отправитель через webhook."""

    async def send(
        self,
        recipient: str,
        subject: str,
        message: str,
        metadata: dict | None = None,
    ) -> SendResult:
        """
        Отправляет POST запрос на webhook URL.

        recipient - это URL вебхука.
        """
        logger.info(
            "Отправка webhook",
            url=recipient[:100],
            subject=subject[:50],
        )

        payload = {
            "subject": subject,
            "message": message,
            "metadata": metadata or {},
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    recipient,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

            if 200 <= response.status_code < 300:
                logger.info("Webhook успешно вызван", url=recipient[:100])
                return SendResult(
                    success=True,
                    message=f"Webhook успешно вызван (status {response.status_code})",
                )
            else:
                logger.warning(
                    "Webhook вернул не-2xx статус",
                    status=response.status_code,
                    body=response.text[:200],
                )
                return SendResult(
                    success=False,
                    message=f"Webhook вернул HTTP {response.status_code}",
                    error_details=response.text[:500],
                )

        except httpx.TimeoutException:
            logger.error("Таймаут при вызове webhook", url=recipient[:100])
            return SendResult(
                success=False,
                message="Таймаут при вызове webhook",
                error_details="Request timed out after 30s",
            )
        except Exception as exc:
            logger.exception("Ошибка при вызове webhook", url=recipient[:100])
            return SendResult(
                success=False,
                message="Не удалось вызвать webhook",
                error_details=str(exc),
            )
