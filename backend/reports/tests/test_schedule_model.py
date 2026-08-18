import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from reports.models import Report, ReportSchedule


@pytest.fixture
def schedule_org(db, test_user):
    """Организация для тестов расписаний."""
    from organizations.models import Organization, OrganizationMember

    org, _ = Organization.objects.get_or_create(name="Schedule Test Org")
    OrganizationMember.objects.get_or_create(
        organization=org,
        user=test_user,
        defaults={"role": OrganizationMember.Role.OWNER},
    )
    return org


@pytest.mark.django_db
class TestReportScheduleModel:
    """Тесты модели ReportSchedule."""

    def test_create_daily_schedule(self, schedule_org, test_user):
        """Создание daily расписания."""
        schedule = ReportSchedule.objects.create(
            organization=schedule_org,
            report_type=Report.ReportType.SALES,
            frequency=ReportSchedule.Frequency.DAILY,
            run_at_hour=9,
            run_at_minute=0,
            created_by=test_user,
        )

        assert schedule.pk is not None
        assert schedule.is_active is True
        assert schedule.next_run_at is not None

        # next_run_at должен быть в будущем
        assert schedule.next_run_at > timezone.now()

        # Должен быть завтра или сегодня в 9:00
        assert schedule.next_run_at.hour == 9
        assert schedule.next_run_at.minute == 0

    def test_create_weekly_schedule(self, schedule_org, test_user):
        """Создание weekly расписания."""
        schedule = ReportSchedule.objects.create(
            organization=schedule_org,
            report_type=Report.ReportType.SALES,
            frequency=ReportSchedule.Frequency.WEEKLY,
            run_day_of_week=0,  # Понедельник
            run_at_hour=10,
            created_by=test_user,
        )

        assert schedule.next_run_at is not None
        # Должен быть понедельник
        assert schedule.next_run_at.weekday() == 0

    def test_create_monthly_schedule(self, schedule_org, test_user):
        """Создание monthly расписания."""
        schedule = ReportSchedule.objects.create(
            organization=schedule_org,
            report_type=Report.ReportType.FINANCE,
            frequency=ReportSchedule.Frequency.MONTHLY,
            run_day_of_month=1,
            run_at_hour=8,
            created_by=test_user,
        )

        assert schedule.next_run_at is not None
        # Должен быть 1 число
        assert schedule.next_run_at.day == 1

    def test_calculate_next_run_daily(self, schedule_org, test_user):
        """Расчёт next_run для daily."""
        schedule = ReportSchedule(
            organization=schedule_org,
            report_type=Report.ReportType.SALES,
            frequency=ReportSchedule.Frequency.DAILY,
            run_at_hour=12,
            run_at_minute=30,
        )

        next_run = schedule.calculate_next_run()
        now = timezone.now()

        assert next_run > now
        assert next_run.hour == 12
        assert next_run.minute == 30

        # Должно быть не позже чем через 24 часа
        assert (next_run - now).total_seconds() <= 24 * 3600

    def test_calculate_next_run_weekly(self, schedule_org, test_user):
        """Расчёт next_run для weekly."""
        schedule = ReportSchedule(
            organization=schedule_org,
            report_type=Report.ReportType.SALES,
            frequency=ReportSchedule.Frequency.WEEKLY,
            run_day_of_week=4,  # Пятница
            run_at_hour=15,
        )

        next_run = schedule.calculate_next_run()

        assert next_run.weekday() == 4
        assert next_run.hour == 15

    def test_calculate_next_run_monthly(self, schedule_org, test_user):
        """Расчёт next_run для monthly."""
        schedule = ReportSchedule(
            organization=schedule_org,
            report_type=Report.ReportType.FINANCE,
            frequency=ReportSchedule.Frequency.MONTHLY,
            run_day_of_month=15,
            run_at_hour=10,
        )

        next_run = schedule.calculate_next_run()

        assert next_run.day == 15
        assert next_run.hour == 10

    def test_unique_constraint_per_org_report_frequency(self, schedule_org, test_user):
        """Нельзя создать два одинаковых расписания для одной организации."""
        ReportSchedule.objects.create(
            organization=schedule_org,
            report_type=Report.ReportType.SALES,
            frequency=ReportSchedule.Frequency.DAILY,
            created_by=test_user,
        )

        with pytest.raises(IntegrityError):
            ReportSchedule.objects.create(
                organization=schedule_org,
                report_type=Report.ReportType.SALES,
                frequency=ReportSchedule.Frequency.DAILY,
                created_by=test_user,
            )

    def test_can_create_different_frequencies(self, schedule_org, test_user):
        """Можно создать разные частоты для одного типа отчёта."""
        daily = ReportSchedule.objects.create(
            organization=schedule_org,
            report_type=Report.ReportType.SALES,
            frequency=ReportSchedule.Frequency.DAILY,
            created_by=test_user,
        )
        weekly = ReportSchedule.objects.create(
            organization=schedule_org,
            report_type=Report.ReportType.SALES,
            frequency=ReportSchedule.Frequency.WEEKLY,
            created_by=test_user,
        )

        assert daily.pk is not None
        assert weekly.pk is not None

    def test_default_values(self, schedule_org, test_user):
        """Проверка значений по умолчанию."""
        schedule = ReportSchedule.objects.create(
            organization=schedule_org,
            report_type=Report.ReportType.SALES,
            created_by=test_user,
        )

        assert schedule.frequency == ReportSchedule.Frequency.MONTHLY
        assert schedule.is_active is True
        assert schedule.run_at_hour == 9
        assert schedule.run_at_minute == 0
        assert schedule.run_day_of_month == 1

    def test_validation_hour_range(self, schedule_org, test_user):
        """Валидация часа (0-23)."""
        with pytest.raises(ValidationError):
            schedule = ReportSchedule(
                organization=schedule_org,
                report_type=Report.ReportType.SALES,
                run_at_hour=25,  # Неверно
            )
            schedule.full_clean()

    def test_validation_day_of_month_range(self, schedule_org, test_user):
        """Валидация дня месяца (1-28)."""
        with pytest.raises(ValidationError):
            schedule = ReportSchedule(
                organization=schedule_org,
                report_type=Report.ReportType.SALES,
                frequency=ReportSchedule.Frequency.MONTHLY,
                run_day_of_month=31,  # Слишком много
            )
            schedule.full_clean()
