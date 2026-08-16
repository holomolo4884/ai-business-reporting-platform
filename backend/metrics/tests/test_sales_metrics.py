import pytest


@pytest.mark.django_db
class TestSalesMetrics:
    """Тесты метрик продаж."""

    def test_total_orders_count(self, metrics_service, sample_orders):
        """Проверяет общее количество заказов в периоде."""
        sales = metrics_service.collect_sales_metrics()

        # 5 заказов в периоде (3 paid + 1 pending + 1 cancelled)
        # 1 заказ вне периода не считается
        assert sales["total_orders"] == 5

    def test_paid_orders_count(self, metrics_service, sample_orders):
        """Проверяет количество оплаченных заказов."""
        sales = metrics_service.collect_sales_metrics()

        assert sales["paid_orders"] == 3

    def test_pending_orders_count(self, metrics_service, sample_orders):
        """Проверяет количество ожидающих заказов."""
        sales = metrics_service.collect_sales_metrics()

        assert sales["pending_orders"] == 1

    def test_cancelled_orders_count(self, metrics_service, sample_orders):
        """Проверяет количество отменённых заказов."""
        sales = metrics_service.collect_sales_metrics()

        assert sales["cancelled_orders"] == 1

    def test_total_revenue(self, metrics_service, sample_orders):
        """Проверяет выручку (только оплаченные заказы)."""
        sales = metrics_service.collect_sales_metrics()

        # 100 + 200 + 300 = 600
        assert sales["total_revenue"] == 600.0

    def test_average_order_value(self, metrics_service, sample_orders):
        """Проверяет средний чек."""
        sales = metrics_service.collect_sales_metrics()

        # (100 + 200 + 300) / 3 = 200
        assert sales["average_order_value"] == 200.0

    def test_orders_by_status(self, metrics_service, sample_orders):
        """Проверяет распределение заказов по статусам."""
        sales = metrics_service.collect_sales_metrics()

        assert sales["orders_by_status"]["paid"] == 3
        assert sales["orders_by_status"]["pending"] == 1
        assert sales["orders_by_status"]["cancelled"] == 1
        assert sales["orders_by_status"]["refunded"] == 0

    def test_empty_period(self, metrics_service):
        """Проверяет метрики за период без данных."""
        sales = metrics_service.collect_sales_metrics()

        assert sales["total_orders"] == 0
        assert sales["paid_orders"] == 0
        assert sales["total_revenue"] == 0.0
        assert sales["average_order_value"] == 0.0
