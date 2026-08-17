from datetime import timedelta

import pytest
from django.utils import timezone

from business_data.models import Currency, Expense, Order
from reports.models import Report
from reports.tasks import generate_report_task


@pytest.fixture
def report_organization(db, test_user):
    """Организация для тестов отчётов."""
    from organizations.models import Organization, OrganizationMember  # noqa: E402

    org = Organization.objects.create(
        name="Report Test Org",
        description="Organization for report testing",
    )
    OrganizationMember.objects.create(
        organization=org,
        user=test_user,
        role=OrganizationMember.Role.OWNER,
    )
    return org


@pytest.fixture
def report_period():
    """Период для тестов отчёта."""
    now = timezone.now()
    return {
        "start": now - timedelta(days=30),
        "end": now,
    }


@pytest.fixture
def test_report(db, report_organization, test_user, report_period):
    """Тестовый отчёт."""
    return Report.objects.create(
        organization=report_organization,
        created_by=test_user,
        report_type=Report.ReportType.SALES,
        status=Report.Status.PENDING,
        period_start=report_period["start"],
        period_end=report_period["end"],
    )


@pytest.fixture
def report_business_data(db, report_organization, report_period):
    """Тестовые бизнес-данные для отчёта."""
    # Заказы
    Order.objects.create(
        organization=report_organization,
        amount=1000.00,
        currency=Currency.USD,
        status=Order.Status.PAID,
        order_date=report_period["start"] + timedelta(days=5),
        description="Test order 1",
    )
    Order.objects.create(
        organization=report_organization,
        amount=2000.00,
        currency=Currency.USD,
        status=Order.Status.PAID,
        order_date=report_period["start"] + timedelta(days=10),
        description="Test order 2",
    )

    # Расходы
    Expense.objects.create(
        organization=report_organization,
        amount=500.00,
        currency=Currency.USD,
        category=Expense.Category.MARKETING,
        expense_date=report_period["start"] + timedelta(days=7),
        description="Test expense",
    )


@pytest.mark.django_db
class TestGenerateReportTask:
    """Тесты задачи generate_report_task."""

    def test_successful_report_generation(self, test_report, report_business_data):
        """Успешная генерация отчёта."""
        # Вызываем задачу
        generate_report_task(test_report.id)

        # Обновляем из БД
        test_report.refresh_from_db()

        # Проверяем статус
        assert test_report.status == Report.Status.COMPLETED
        assert test_report.completed_at is not None

        # Проверяем метрики
        assert test_report.metrics != {}
        assert "sales" in test_report.metrics
        assert "finance" in test_report.metrics
        assert test_report.metrics["sales"]["total_orders"] == 2
        assert test_report.metrics["finance"]["total_revenue"] == 3000.0
        assert test_report.metrics["finance"]["total_expenses"] == 500.0
        assert test_report.metrics["finance"]["net_profit"] == 2500.0

        # Проверяем AI ответ (заглушка)
        assert test_report.ai_response != {}
        assert test_report.generated_text != ""

        # Проверяем отсутствие ошибки
        assert test_report.error == ""

    def test_report_generation_with_empty_data(self, test_report):
        """Генерация отчёта без бизнес-данных."""
        generate_report_task(test_report.id)

        test_report.refresh_from_db()

        assert test_report.status == Report.Status.COMPLETED
        assert test_report.completed_at is not None
        assert test_report.metrics["sales"]["total_orders"] == 0
        assert test_report.metrics["finance"]["total_revenue"] == 0.0
        assert test_report.metrics["finance"]["total_expenses"] == 0.0
        assert test_report.metrics["finance"]["net_profit"] == 0.0

    def test_report_generation_with_nonexistent_report(self):
        """Генерация несуществующего отчёта не вызывает ошибку."""
        # Задача должна корректно обработать отсутствие отчёта
        generate_report_task(99999)

    def test_report_status_transitions(self, test_report, report_business_data):
        """Проверяет последовательную смену статусов."""
        # Начальный статус
        assert test_report.status == Report.Status.PENDING

        # Запускаем задачу
        generate_report_task(test_report.id)

        # Финальный статус
        test_report.refresh_from_db()
        assert test_report.status == Report.Status.COMPLETED
