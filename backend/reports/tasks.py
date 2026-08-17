import logging

from celery import shared_task
from django.utils import timezone

from metrics.services import MetricsService
from reports.models import Report

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    autoretry_for=(Exception,),
)
def generate_report_task(self, report_id: int) -> None:
    """
    Главная задача генерации отчёта.

    Шаги:
    1. Получает Report из БД
    2. Собирает метрики через MetricsService
    3. Вызывает AI для генерации текста
    4. Сохраняет результат
    5. Обновляет статус
    """
    logger.info("Начало генерации отчёта #%s (попытка %s)", report_id, self.request.retries + 1)

    try:
        # Получаем отчёт
        report = Report.objects.select_related("organization").get(id=report_id)
    except Report.DoesNotExist:
        logger.error("Отчёт #%s не найден", report_id)
        return

    try:
        # Шаг 1: Сбор метрик
        _collect_metrics(report)

        # Шаг 2: Вызов AI
        _call_ai(report)

        # Шаг 3: Генерация PDF
        _generate_pdf(report)

        # Шаг 4: Завершение
        report.status = Report.Status.COMPLETED
        report.completed_at = timezone.now()
        report.save()

        logger.info("Отчёт #%s успешно сгенерирован", report_id)

        # Шаг 5: Отправка уведомления
        try:
            from notifications.tasks import send_report_notification_task  # noqa: E402

            send_report_notification_task.delay(report.id, channel="email")
            logger.info("Задача уведомления для отчёта #%s поставлена в очередь", report_id)
        except Exception as exc:
            # Не прерываем выполнение из-за ошибки отправки уведомления
            logger.exception(
                "Не удалось поставить задачу уведомления для отчёта #%s: %s",
                report_id,
                exc,
            )

    except Exception as exc:
        logger.exception("Ошибка при генерации отчёта #%s: %s", report_id, exc)

        # Обновляем статус на failed
        report.status = Report.Status.FAILED
        report.error = str(exc)
        report.save()

        # Если это временная ошибка — повторяем
        if self.request.retries < self.max_retries:
            logger.info("Повторная попытка генерации отчёта #%s", report_id)
            raise self.retry(exc=exc) from exc

        logger.error("Превышено количество попыток для отчёта #%s", report_id)


def _collect_metrics(report: Report) -> None:
    """Собирает метрики и сохраняет их в Report."""
    logger.info("Сбор метрик для отчёта #%s", report.id)

    report.status = Report.Status.COLLECTING_DATA
    report.save()

    service = MetricsService(
        organization=report.organization,
        period_start=report.period_start,
        period_end=report.period_end,
    )

    metrics = service.collect_all_metrics()
    report.metrics = metrics
    report.save()

    logger.info("Метрики собраны для отчёта #%s", report.id)


def _call_ai(report: Report) -> None:
    """
    Вызывает AI для генерации текста отчёта и рендерит финальный текст.
    """
    logger.info("Вызов AI для отчёта #%s", report.id)

    report.status = Report.Status.CALLING_AI
    report.save()

    # Используем AIClient для вызова AI
    from ai.client import AIClient  # noqa: E402

    client = AIClient()
    ai_response = client.generate_report(report)

    # Сохраняем AI ответ
    report.ai_response = ai_response

    # Рендерим финальный текст с помощью ReportRenderer
    from reports.renderers import ReportRenderer  # noqa: E402

    renderer = ReportRenderer(report)
    report.generated_text = renderer.render_text()
    report.generated_html = renderer.render_html()

    report.save()

    logger.info("AI ответ получен и отрендерен для отчёта #%s", report.id)


def _generate_pdf(report: Report) -> None:
    """Генерирует PDF файл отчёта и сохраняет его."""
    logger.info("Генерация PDF для отчёта #%s", report.id)

    try:
        from reports.renderers import ReportRenderer  # noqa: E402

        renderer = ReportRenderer(report)
        pdf_bytes = renderer.render_pdf()

        # Сохраняем PDF в FileField
        from django.core.files.base import ContentFile

        filename = f"report_{report.id}.pdf"
        report.pdf_file.save(filename, ContentFile(pdf_bytes), save=False)
        report.save()

        logger.info("PDF сохранён для отчёта #%s: %s", report.id, filename)

    except Exception as exc:
        logger.exception("Ошибка при генерации PDF для отчёта #%s", report.id)
        # Не прерываем генерацию отчёта из-за ошибки PDF
        report.error = f"Ошибка генерации PDF: {exc}"
        report.save()
