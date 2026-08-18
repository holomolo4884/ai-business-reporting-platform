from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from reports.models import Report, ReportSchedule
from reports.tasks import (
    _calculate_report_period,
    check_and_run_scheduled_reports_task,
)


@pytest.fixture(autouse=True)
def clean_schedules(db):
    """
    Очищает все расписания перед каждым тестом.

    Гарантирует изоляцию тестов — каждый тест работает
    только со своими данными.
    """
    ReportSchedule.objects.all().delete()
    yield
    ReportSchedule.objects.all().delete()


@pytest.fixture
def schedule_org(db, test_user):
    """Организация для тестов расписаний."""
    from organizations.models import Organization, OrganizationMember

    org, _ = Organization.objects.get_or_create(name="Schedule Task Test Org")
    OrganizationMember.objects.get_or_create(
        organization=org,
        user=test_user,
        defaults={"role": OrganizationMember.Role.OWNER},
    )
    return org


@pytest.fixture
def schedule_for_task(schedule_org, test_user):
    """Активное расписание для тестов задачи."""
    schedule = ReportSchedule.objects.create(
        organization=schedule_org,
        report_type=Report.ReportType.SALES,
        frequency=ReportSchedule.Frequency.DAILY,
        run_at_hour=9,
        run_at_minute=0,
        created_by=test_user,
        is_active=True,
    )
    # Устанавливаем next_run_at в прошлое, чтобы задача сработала
    schedule.next_run_at = timezone.now() - timedelta(minutes=5)
    schedule.save()
    return schedule


@pytest.mark.django_db
class TestCalculateReportPeriod:
    """Тесты функции _calculate_report_period."""

    def test_daily_period(self, schedule_for_task):
        """Daily возвращает предыдущий день."""
        now = timezone.now()
        start, end = _calculate_report_period(schedule_for_task, now)

        assert start.date() == (now.date() - timedelta(days=1))
        assert end.date() == (now.date() - timedelta(days=1))
        assert start.hour == 0
        assert end.hour == 23

    def test_weekly_period(self, schedule_for_task):
        """Weekly возвращает предыдущую неделю (Пн-Вс)."""
        schedule_for_task.frequency = ReportSchedule.Frequency.WEEKLY
        schedule_for_task.save()

        now = timezone.now()
        start, end = _calculate_report_period(schedule_for_task, now)

        # Начало — понедельник предыдущей недели
        assert start.weekday() == 0  # Понедельник
        # Конец — воскресенье предыдущей недели
        assert end.weekday() == 6  # Воскресенье
        # Разница — 6 дней
        assert (end.date() - start.date()).days == 6

    def test_monthly_period(self, schedule_for_task):
        """Monthly возвращает предыдущий месяц."""
        schedule_for_task.frequency = ReportSchedule.Frequency.MONTHLY
        schedule_for_task.save()

        now = timezone.now()
        start, end = _calculate_report_period(schedule_for_task, now)

        # Первый день предыдущего месяца
        assert start.day == 1
        # Последний день предыдущего месяца
        import calendar

        _, last_day = calendar.monthrange(end.year, end.month)
        assert end.day == last_day


@pytest.mark.django_db
class TestCheckAndRunScheduledReportsTask:
    """Тесты check_and_run_scheduled_reports_task."""

    @patch("reports.tasks.generate_report_task.delay")
    def test_creates_report_for_due_schedule(self, mock_delay, schedule_for_task):
        """Задача создаёт отчёт для расписания с подошедшим временем."""
        stats = check_and_run_scheduled_reports_task()

        assert stats["processed"] == 1
        assert stats["created"] == 1
        assert stats["skipped"] == 0
        assert stats["errors"] == 0

        # Проверяем, что generate_report_task был вызван
        mock_delay.assert_called_once()
        report_id = mock_delay.call_args[0][0]

        # Проверяем, что отчёт создан
        report = Report.objects.get(id=report_id)
        assert report.organization == schedule_for_task.organization
        assert report.report_type == schedule_for_task.report_type
        assert report.status == Report.Status.PENDING

    @patch("reports.tasks.generate_report_task.delay")
    def test_skips_inactive_schedule(self, mock_delay, schedule_for_task):
        """Задача пропускает неактивные расписания."""
        schedule_for_task.is_active = False
        schedule_for_task.save()

        stats = check_and_run_scheduled_reports_task()

        assert stats["processed"] == 0
        assert stats["created"] == 0
        mock_delay.assert_not_called()

    @patch("reports.tasks.generate_report_task.delay")
    def test_skips_future_schedule(self, mock_delay, schedule_for_task):
        """Задача пропускает расписания, у которых ещё не пришло время."""
        schedule_for_task.next_run_at = timezone.now() + timedelta(hours=1)
        schedule_for_task.save()

        stats = check_and_run_scheduled_reports_task()

        assert stats["processed"] == 0
        mock_delay.assert_not_called()

    @patch("reports.tasks.generate_report_task.delay")
    def test_prevents_duplicate_reports(self, mock_delay, schedule_for_task):
        """Задача не создаёт дубликаты отчётов за один период."""
        # Первый запуск — создаётся отчёт
        stats1 = check_and_run_scheduled_reports_task()
        assert stats1["created"] == 1

        # Сбрасываем next_run_at в прошлое снова
        schedule_for_task.refresh_from_db()
        schedule_for_task.next_run_at = timezone.now() - timedelta(minutes=5)
        schedule_for_task.save()

        mock_delay.reset_mock()

        # Второй запуск — должен пропустить (дубликат)
        stats2 = check_and_run_scheduled_reports_task()
        assert stats2["processed"] == 1
        assert stats2["created"] == 0
        assert stats2["skipped"] == 1
        mock_delay.assert_not_called()

    @patch("reports.tasks.generate_report_task.delay")
    def test_updates_schedule_after_execution(self, mock_delay, schedule_for_task):
        """Задача обновляет last_run_at и next_run_at."""
        old_next_run = schedule_for_task.next_run_at

        check_and_run_scheduled_reports_task()

        schedule_for_task.refresh_from_db()
        assert schedule_for_task.last_run_at is not None
        assert schedule_for_task.next_run_at > old_next_run
        assert schedule_for_task.next_run_at > timezone.now()

    @patch("reports.tasks.generate_report_task.delay")
    def test_handles_multiple_schedules(self, mock_delay, schedule_for_task, test_user):
        """Задача обрабатывает несколько расписаний."""
        from organizations.models import Organization, OrganizationMember

        # Создаём вторую организацию и делаем test_user её owner
        org2 = Organization.objects.create(name="Second Org")
        OrganizationMember.objects.create(
            organization=org2,
            user=test_user,
            role=OrganizationMember.Role.OWNER,
        )

        ReportSchedule.objects.create(
            organization=org2,
            report_type=Report.ReportType.FINANCE,
            frequency=ReportSchedule.Frequency.DAILY,
            run_at_hour=10,
            created_by=test_user,
            is_active=True,
            next_run_at=timezone.now() - timedelta(minutes=5),
        )

        stats = check_and_run_scheduled_reports_task()

        assert stats["processed"] == 2
        assert stats["created"] == 2
        assert mock_delay.call_count == 2

    def test_no_schedules_returns_empty_stats(self):
        """Если нет расписаний, возвращается пустая статистика."""
        # clean_schedules уже очистила все расписания

        stats = check_and_run_scheduled_reports_task()

        assert stats["processed"] == 0
        assert stats["created"] == 0
        assert stats["skipped"] == 0
        assert stats["errors"] == 0
