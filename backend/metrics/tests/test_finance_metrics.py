import pytest


@pytest.mark.django_db
class TestFinanceMetrics:
    """Тесты финансовых метрик."""

    def test_total_revenue(self, metrics_service, sample_orders, sample_expenses):
        """Проверяет выручку в финансовых метриках."""
        finance = metrics_service.collect_finance_metrics()

        # Только оплаченные заказы: 100 + 200 + 300 = 600
        assert finance["total_revenue"] == 600.0

    def test_total_expenses(self, metrics_service, sample_orders, sample_expenses):
        """Проверяет общую сумму расходов."""
        finance = metrics_service.collect_finance_metrics()

        # 1000 + 5000 + 500 + 300 + 200 = 7000
        # Расход вне периода (9999) не считается
        assert finance["total_expenses"] == 7000.0

    def test_net_profit(self, metrics_service, sample_orders, sample_expenses):
        """Проверяет чистую прибыль."""
        finance = metrics_service.collect_finance_metrics()

        # 600 - 7000 = -6400
        assert finance["net_profit"] == -6400.0

    def test_profit_margin(self, metrics_service, sample_orders, sample_expenses):
        """Проверяет маржу прибыли."""
        finance = metrics_service.collect_finance_metrics()

        # (-6400 / 600) * 100 = -1066.67%
        assert finance["profit_margin"] == -1066.67

    def test_is_profitable(self, metrics_service, sample_orders, sample_expenses):
        """Проверяет флаг прибыльности."""
        finance = metrics_service.collect_finance_metrics()

        # Прибыль отрицательная
        assert finance["is_profitable"] is False

    def test_expenses_count(self, metrics_service, sample_orders, sample_expenses):
        """Проверяет количество расходов."""
        finance = metrics_service.collect_finance_metrics()

        # 5 расходов в периоде
        assert finance["expenses_count"] == 5

    def test_empty_period(self, metrics_service):
        """Проверяет финансовые метрики за период без данных."""
        finance = metrics_service.collect_finance_metrics()

        assert finance["total_revenue"] == 0.0
        assert finance["total_expenses"] == 0.0
        assert finance["net_profit"] == 0.0
        assert finance["profit_margin"] == 0.0
        assert finance["is_profitable"] is False
