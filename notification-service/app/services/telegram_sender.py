import httpx
from structlog import get_logger

from app.config import settings
from app.services.base import BaseSender, SendResult

logger = get_logger()

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/{method}"


class TelegramSender(BaseSender):
    """Отправитель через Telegram."""

    async def send(
        self,
        recipient: str,
        subject: str,
        message: str,
        metadata: dict | None = None,
    ) -> SendResult:
        """
        Отправляет сообщение в Telegram.

        recipient - это chat_id (например, "123456789" или "@username").
        """
        logger.info(
            "Отправка Telegram",
            chat_id=recipient,
            subject=subject[:50],
        )

        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram bot token не настроен, fake режим")
            return SendResult(
                success=True,
                message=f"Telegram сообщение отправлено (fake): {recipient}",
            )

        # Формируем финальное сообщение
        text = f"*{subject}*\n\n{message}" if subject else message

        try:
            url = TELEGRAM_API_URL.format(
                token=settings.TELEGRAM_BOT_TOKEN,
                method="sendMessage",
            )

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json={
                        "chat_id": recipient,
                        "text": text,
                        "parse_mode": "Markdown",
                    },
                )

            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    logger.info("Telegram сообщение отправлено", chat_id=recipient)
                    return SendResult(
                        success=True,
                        message=f"Telegram сообщение отправлено в {recipient}",
                    )
                else:
                    error_desc = data.get("description", "неизвестная ошибка")
                    logger.error(
                        "Telegram API вернул ошибку",
                        chat_id=recipient,
                        error=error_desc,
                    )
                    return SendResult(
                        success=False,
                        message="Telegram API вернул ошибку",
                        error_details=error_desc,
                    )
            else:
                logger.error(
                    "Ошибка HTTP от Telegram API",
                    status=response.status_code,
                    body=response.text[:200],
                )
                return SendResult(
                    success=False,
                    message=f"Telegram API HTTP {response.status_code}",
                    error_details=response.text[:500],
                )

        except httpx.TimeoutException:
            logger.error("Таймаут при отправке в Telegram", chat_id=recipient)
            return SendResult(
                success=False,
                message="Таймаут при отправке в Telegram",
                error_details="Request timed out after 30s",
            )
        except Exception as exc:
            logger.exception("Ошибка при отправке в Telegram", chat_id=recipient)
            return SendResult(
                success=False,
                message="Не удалось отправить в Telegram",
                error_details=str(exc),
            )
