import logging
from datetime import UTC, datetime, timedelta

from celery import shared_task
from django.utils import timezone

from metrics.services import MetricsService
from reports.models import Report, ReportSchedule

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


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def check_and_run_scheduled_reports_task(self) -> dict:
    """
    Периодическая задача, проверяющая расписания и запускающая генерацию отчётов.

    Запускается Celery Beat каждую минуту.

    Шаги:
    1. Находит все активные расписания, у которых next_run_at <= now
    2. Для каждого расписания:
       - Рассчитывает период отчёта (предыдущий день/неделя/месяц)
       - Проверяет, нет ли уже отчёта за этот период (защита от дублирования)
       - Создаёт новый отчёт
       - Запускает generate_report_task
       - Обновляет last_run_at и next_run_at

    Returns:
        dict: Статистика выполнения (processed, created, skipped).
    """

    logger.info("Запуск проверки расписаний отчётов")

    now = timezone.now()
    stats = {"processed": 0, "created": 0, "skipped": 0, "errors": 0}

    # Находим все активные расписания, у которых пришло время запускаться
    schedules = ReportSchedule.objects.filter(
        is_active=True,
        next_run_at__lte=now,
    ).select_related("organization", "created_by")

    if not schedules.exists():
        logger.info("Нет расписаний, требующих запуска")
        return stats

    logger.info("Найдено %d расписаний для обработки", schedules.count())

    for schedule in schedules:
        try:
            stats["processed"] += 1

            # Рассчитываем период для отчёта
            period_start, period_end = _calculate_report_period(schedule, now)

            # Проверяем дублирование
            existing_report = Report.objects.filter(
                organization=schedule.organization,
                report_type=schedule.report_type,
                period_start=period_start,
                period_end=period_end,
            ).exists()

            if existing_report:
                logger.info(
                    "Отчёт за период %s - %s уже существует, пропускаем расписание #%s",
                    period_start,
                    period_end,
                    schedule.id,
                )
                stats["skipped"] += 1
                # Всё равно обновляем next_run_at, чтобы не пытаться снова
                _advance_schedule(schedule)
                continue

            # Создаём отчёт
            report = Report.objects.create(
                organization=schedule.organization,
                created_by=schedule.created_by,
                report_type=schedule.report_type,
                status=Report.Status.PENDING,
                period_start=period_start,
                period_end=period_end,
            )

            # Запускаем генерацию
            generate_report_task.delay(report.id)

            logger.info(
                "Запущена генерация отчёта #%s по расписанию #%s (период %s - %s)",
                report.id,
                schedule.id,
                period_start,
                period_end,
            )

            stats["created"] += 1

            # Обновляем расписание
            _advance_schedule(schedule)

        except Exception as exc:
            logger.exception(
                "Ошибка при обработке расписания #%s: %s",
                schedule.id,
                exc,
            )
            stats["errors"] += 1

    logger.info(
        "Проверка расписаний завершена: processed=%d, created=%d, skipped=%d, errors=%d",
        stats["processed"],
        stats["created"],
        stats["skipped"],
        stats["errors"],
    )

    return stats


def _calculate_report_period(
    schedule: ReportSchedule,
    now: datetime,
) -> tuple[datetime, datetime]:
    """
    Рассчитывает период отчёта на основе частоты расписания.

    Отчёт всегда охватывает ПРЕДЫДУЩИЙ период:
    - DAILY: предыдущий день
    - WEEKLY: предыдущая неделя (Пн-Вс)
    - MONTHLY: предыдущий месяц

    Returns:
        tuple: (period_start, period_end) с timezone UTC.
    """
    if schedule.frequency == ReportSchedule.Frequency.DAILY:
        # Предыдущий полный день
        yesterday = now.date() - timedelta(days=1)
        period_start = datetime.combine(
            yesterday,
            datetime.min.time(),
            tzinfo=UTC,
        )
        period_end = datetime.combine(
            yesterday,
            datetime.max.time(),
            tzinfo=UTC,
        )
        return period_start, period_end

    if schedule.frequency == ReportSchedule.Frequency.WEEKLY:
        # Предыдущая полная неделя (Пн-Вс)
        # Находим начало текущей недели (понедельник)
        current_week_start = now.date() - timedelta(days=now.weekday())
        # Предыдущая неделя
        prev_week_start = current_week_start - timedelta(weeks=1)
        prev_week_end = prev_week_start + timedelta(days=6)

        period_start = datetime.combine(
            prev_week_start,
            datetime.min.time(),
            tzinfo=UTC,
        )
        period_end = datetime.combine(
            prev_week_end,
            datetime.max.time(),
            tzinfo=UTC,
        )
        return period_start, period_end

    if schedule.frequency == ReportSchedule.Frequency.MONTHLY:
        # Предыдущий полный месяц

        # Первый день текущего месяца
        current_month_start = now.date().replace(day=1)
        # Последний день предыдущего месяца
        prev_month_end = current_month_start - timedelta(days=1)
        # Первый день предыдущего месяца
        prev_month_start = prev_month_end.replace(day=1)

        period_start = datetime.combine(
            prev_month_start,
            datetime.min.time(),
            tzinfo=UTC,
        )
        period_end = datetime.combine(
            prev_month_end,
            datetime.max.time(),
            tzinfo=UTC,
        )
        return period_start, period_end

    # Fallback — предыдущий день
    yesterday = now.date() - timedelta(days=1)
    return (
        datetime.combine(yesterday, datetime.min.time(), tzinfo=UTC),
        datetime.combine(yesterday, datetime.max.time(), tzinfo=UTC),
    )


def _advance_schedule(schedule: ReportSchedule) -> None:
    """
    Обновляет расписание после выполнения:
    - last_run_at = сейчас
    - next_run_at = следующее время запуска
    """
    schedule.last_run_at = timezone.now()
    schedule.next_run_at = schedule.calculate_next_run()
    schedule.save(update_fields=["last_run_at", "next_run_at"])
