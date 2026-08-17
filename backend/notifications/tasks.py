import logging
from typing import Any

from celery import shared_task
from django.utils import timezone

from notifications.client import NotificationClient, NotificationError
from notifications.models import NotificationLog
from reports.models import Report

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(Exception,),
    acks_late=True,
)
def send_report_notification_task(
    self,
    report_id: int,
    channel: str = "email",
) -> None:
    """
    Отправляет уведомление о завершении генерации отчёта.
    """
    logger.info(
        "Отправка уведомления об отчёте #%s (попытка %s)",
        report_id,
        self.request.retries + 1,
    )

    try:
        report = Report.objects.select_related("organization", "created_by").get(id=report_id)
    except Report.DoesNotExist:
        logger.error("Отчёт #%s не найден, отправка уведомления невозможна", report_id)
        return

    # Получаем получателя
    user = report.created_by
    if not user:
        logger.warning("У отчёта #%s нет создателя, некому отправлять", report_id)
        return

    # Определяем канал и получателя
    from notifications.client import NotificationChannel

    if channel == "telegram":
        # TODO: брать chat_id из профиля пользователя
        recipient = user.email
        notification_channel = NotificationChannel.EMAIL
    else:
        recipient = user.email
        notification_channel = NotificationChannel.EMAIL

    if not recipient:
        logger.warning(
            "У пользователя %s нет email для отправки уведомления",
            user.id,
        )
        return

    # Формируем сообщение
    subject = f"Отчёт готов: {report.organization.name}"
    period_start = report.period_start.strftime("%d.%m.%Y")
    period_end = report.period_end.strftime("%d.%m.%Y")

    message = (
        f"Ваш отчёт успешно сгенерирован.\n\n"
        f"Организация: {report.organization.name}\n"
        f"Тип: {report.report_type}\n"
        f"Период: {period_start} — {period_end}\n\n"
        f"Вы можете скачать PDF отчёт в личном кабинете."
    )

    # Создаём лог
    log = NotificationLog.objects.create(
        channel=notification_channel.value,
        recipient=recipient,
        subject=subject,
        message=message,
        status=NotificationLog.Status.PENDING,
        user=user,
        report=report,
        metadata={"report_type": report.report_type},
    )

    # Отправляем уведомление
    try:
        client = NotificationClient()
        response = client.send_notification(
            channel=notification_channel,
            recipient=recipient,
            subject=subject,
            message=message,
            metadata={"report_id": report.id},
        )

        if response.success:
            log.status = NotificationLog.Status.SUCCESS
            log.notification_id = response.notification_id or ""
            log.sent_at = timezone.now()
            log.attempts = self.request.retries + 1
            log.save()
            logger.info(
                "Уведомление об отчёте #%s успешно отправлено (log_id=%s)",
                report_id,
                log.id,
            )
        else:
            log.status = NotificationLog.Status.FAILED
            log.error_details = response.error_details or response.message
            log.attempts = self.request.retries + 1
            log.save()
            logger.warning(
                "Ошибка отправки уведомления об отчёте #%s: %s",
                report_id,
                response.message,
            )
            if self.request.retries < self.max_retries:
                raise self.retry(exc=NotificationError(response.message))

    except NotificationError as exc:
        log.status = NotificationLog.Status.FAILED
        log.error_details = str(exc)
        log.attempts = self.request.retries + 1
        log.save()
        logger.exception(
            "Ошибка NotificationError при отправке уведомления об отчёте #%s",
            report_id,
        )
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc) from None

    except Exception as exc:
        log.status = NotificationLog.Status.FAILED
        log.error_details = str(exc)
        log.attempts = self.request.retries + 1
        log.save()
        logger.exception(
            "Неожиданная ошибка при отправке уведомления об отчёте #%s",
            report_id,
        )
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc) from None


@shared_task
def send_simple_notification(
    channel: str,
    recipient: str,
    message: str,
    subject: str = "",
    metadata: dict[str, Any] | None = None,
) -> None:
    """Простая задача для отправки одиночного уведомления."""
    from notifications.client import NotificationChannel  # noqa: E402

    log = NotificationLog.objects.create(
        channel=channel,
        recipient=recipient,
        subject=subject,
        message=message,
        status=NotificationLog.Status.PENDING,
        metadata=metadata or {},
    )

    try:
        client = NotificationClient()
        response = client.send_notification(
            channel=NotificationChannel(channel),
            recipient=recipient,
            subject=subject,
            message=message,
            metadata=metadata,
        )

        if response.success:
            log.status = NotificationLog.Status.SUCCESS
            log.notification_id = response.notification_id or ""
            log.sent_at = timezone.now()
            log.attempts = 1
        else:
            log.status = NotificationLog.Status.FAILED
            log.error_details = response.error_details or response.message
            log.attempts = 1

    except Exception as exc:
        log.status = NotificationLog.Status.FAILED
        log.error_details = str(exc)
        log.attempts = 1
        logger.exception("Ошибка при отправке простого уведомления")

    log.save()
