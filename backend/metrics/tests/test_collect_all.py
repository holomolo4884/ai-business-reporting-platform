import pytest

from metrics.services import MetricsService


@pytest.mark.django_db
class TestCollectAllMetrics:
    """Тесты collect_all_metrics."""

    def test_collect_all_metrics_structure(self, metrics_service, sample_orders, sample_expenses):
        """Проверяет структуру collect_all_metrics."""
        metrics = metrics_service.collect_all_metrics()

        assert "period" in metrics
        assert "sales" in metrics
        assert "finance" in metrics
        assert "top_expense_categories" in metrics
        assert "period_comparison" not in metrics  # Не включено по умолчанию

    def test_collect_all_metrics_with_comparison(
        self, metrics_service, sample_orders, sample_expenses
    ):
        """Проверяет collect_all_metrics со сравнением периодов."""
        metrics = metrics_service.collect_all_metrics(include_comparison=True)

        assert "period_comparison" in metrics
        comparison = metrics["period_comparison"]
        assert "current_period" in comparison
        assert "previous_period" in comparison
        assert "changes" in comparison

    def test_period_comparison_structure(self, metrics_service, sample_orders, sample_expenses):
        """Проверяет структуру сравнения периодов."""
        comparison = metrics_service.collect_period_comparison()

        assert comparison["current_period"]["revenue"] == 600.0
        assert comparison["current_period"]["orders_count"] == 5

        # Предыдущий период: данных нет (мы не создавали заказы за 60-30 дней)
        assert comparison["previous_period"]["revenue"] == 0.0
        assert comparison["previous_period"]["orders_count"] == 0

        # Изменение выручки: None, так как предыдущее значение 0
        assert comparison["changes"]["revenue_change"] is None


@pytest.mark.django_db
class TestTimezoneHandling:
    """Тесты обработки таймзон."""

    def test_naive_datetime_conversion(self, metrics_organization, period):
        """Проверяет, что naive datetime конвертируется в aware."""
        from datetime import datetime

        from django.utils import timezone

        naive_start = datetime(2026, 7, 1, 0, 0, 0)
        naive_end = datetime(2026, 7, 31, 23, 59, 59)

        service = MetricsService(
            organization=metrics_organization,
            period_start=naive_start,
            period_end=naive_end,
        )

        # После конвертации должны быть aware
        assert timezone.is_aware(service.period_start)
        assert timezone.is_aware(service.period_end)
