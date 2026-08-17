import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from structlog import get_logger

from app.config import settings
from app.services.base import BaseSender, SendResult

logger = get_logger()


class EmailSender(BaseSender):
    """Отправитель email через SMTP."""

    async def send(
        self,
        recipient: str,
        subject: str,
        message: str,
        metadata: dict | None = None,
    ) -> SendResult:
        """Отправляет email."""
        logger.info(
            "Отправка email",
            recipient=recipient,
            subject=subject[:50],
        )

        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.warning("SMTP не настроен, используем режим fake")
            return SendResult(
                success=True,
                message=f"Email отправлен (fake режим): {recipient}",
            )

        try:
            # Формируем письмо
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = recipient

            # Добавляем текст (plain text)
            text_part = MIMEText(message, "plain", "utf-8")
            msg.attach(text_part)

            # Пробуем добавить HTML версию (если есть в metadata)
            if metadata and metadata.get("html"):
                html_part = MIMEText(metadata["html"], "html", "utf-8")
                msg.attach(html_part)

            # Отправляем
            if settings.SMTP_USE_TLS:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
                server.starttls()
            else:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)

            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()

            logger.info("Email успешно отправлен", recipient=recipient)

            return SendResult(
                success=True,
                message=f"Email успешно отправлен на {recipient}",
            )

        except Exception as exc:
            logger.exception("Ошибка при отправке email", recipient=recipient)
            return SendResult(
                success=False,
                message="Не удалось отправить email",
                error_details=str(exc),
            )
