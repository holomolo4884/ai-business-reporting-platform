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

        # Шаг 3: Завершение
        report.status = Report.Status.COMPLETED
        report.completed_at = timezone.now()
        report.save()

        logger.info("Отчёт #%s успешно сгенерирован", report_id)

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
    Вызывает AI для генерации текста отчёта.

    Пока это заглушка — полноценная интеграция с AI будет в блоке M.
    """
    logger.info("Вызов AI для отчёта #%s", report.id)

    report.status = Report.Status.CALLING_AI
    report.save()

    # Заглушка: симулируем ответ от AI
    report.ai_response = {
        "summary": "Это заглушка ответа от AI",
        "insights": ["Инсайт 1", "Инсайт 2", "Инсайт 3"],
    }
    report.generated_text = (
        f"Отчёт за период с {report.period_start.date()} по {report.period_end.date()}. "
        f"Общая выручка: {report.metrics.get('finance', {}).get('total_revenue', 0)}. "
        f"Общие расходы: {report.metrics.get('finance', {}).get('total_expenses', 0)}. "
        f"Чистая прибыль: {report.metrics.get('finance', {}).get('net_profit', 0)}."
    )
    report.save()

    logger.info("AI ответ получен для отчёта #%s", report.id)
