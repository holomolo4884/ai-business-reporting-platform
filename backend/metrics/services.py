from datetime import datetime
from decimal import Decimal

from django.db.models import Avg, Count, Sum
from django.db.models.functions import Coalesce

from business_data.models import Expense, Order
from organizations.models import Organization


class MetricsService:
    """Сервис для сбора бизнес-метрик."""

    def __init__(
        self,
        organization: Organization,
        period_start: datetime,
        period_end: datetime,
    ):
        from django.utils import timezone as tz

        # Конвертируем naive datetime в aware, если необходимо
        if tz.is_naive(period_start):
            period_start = tz.make_aware(period_start)
        if tz.is_naive(period_end):
            period_end = tz.make_aware(period_end)

        self.organization = organization
        self.period_start = period_start
        self.period_end = period_end

    def collect_all_metrics(self, include_comparison: bool = False) -> dict:
        """Собирает все метрики для отчёта."""
        sales_metrics = self.collect_sales_metrics()
        finance_metrics = self.collect_finance_metrics()
        top_categories = self.collect_top_categories()

        result = {
            "period": {
                "start": self.period_start.isoformat(),
                "end": self.period_end.isoformat(),
            },
            "sales": sales_metrics,
            "finance": finance_metrics,
            "top_expense_categories": top_categories,
        }

        if include_comparison:
            result["period_comparison"] = self.collect_period_comparison()

        return result

    def collect_sales_metrics(self) -> dict:
        """Собирает метрики продаж."""
        orders = Order.objects.filter(
            organization=self.organization,
            order_date__gte=self.period_start,
            order_date__lte=self.period_end,
        )

        # Общее количество заказов
        total_orders = orders.count()

        # Заказы по статусам
        orders_by_status = {}
        for status_choice in Order.Status.choices:
            status_value = status_choice[0]
            orders_by_status[status_value] = orders.filter(status=status_value).count()

        # Только оплаченные заказы для расчёта выручки
        paid_orders = orders.filter(status=Order.Status.PAID)

        # Выручка (сумма оплаченных заказов)
        revenue_result = paid_orders.aggregate(total=Coalesce(Sum("amount"), Decimal("0")))
        total_revenue = float(revenue_result["total"])

        # Средний чек
        avg_result = paid_orders.aggregate(avg=Coalesce(Avg("amount"), Decimal("0")))
        average_order_value = float(avg_result["avg"])

        return {
            "total_orders": total_orders,
            "paid_orders": orders_by_status.get("paid", 0),
            "pending_orders": orders_by_status.get("pending", 0),
            "cancelled_orders": orders_by_status.get("cancelled", 0),
            "refunded_orders": orders_by_status.get("refunded", 0),
            "total_revenue": total_revenue,
            "average_order_value": round(average_order_value, 2),
            "orders_by_status": orders_by_status,
        }

    def collect_finance_metrics(self) -> dict:
        """Собирает финансовые метрики."""
        # Выручка (сумма оплаченных заказов)
        paid_orders = Order.objects.filter(
            organization=self.organization,
            order_date__gte=self.period_start,
            order_date__lte=self.period_end,
            status=Order.Status.PAID,
        )
        revenue_result = paid_orders.aggregate(total=Coalesce(Sum("amount"), Decimal("0")))
        total_revenue = float(revenue_result["total"])

        # Расходы
        expenses = Expense.objects.filter(
            organization=self.organization,
            expense_date__gte=self.period_start,
            expense_date__lte=self.period_end,
        )
        expenses_result = expenses.aggregate(
            total=Coalesce(Sum("amount"), Decimal("0")),
            count=Count("id"),
        )
        total_expenses = float(expenses_result["total"])
        expenses_count = expenses_result["count"]

        # Прибыль
        net_profit = total_revenue - total_expenses

        # Маржа прибыли
        profit_margin = 0.0
        if total_revenue > 0:
            profit_margin = round((net_profit / total_revenue) * 100, 2)

        return {
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "net_profit": round(net_profit, 2),
            "profit_margin": profit_margin,
            "expenses_count": expenses_count,
            "is_profitable": net_profit > 0,
        }

    def collect_top_categories(self, limit: int = 5) -> list:
        """Собирает топ категорий расходов."""
        expenses = Expense.objects.filter(
            organization=self.organization,
            expense_date__gte=self.period_start,
            expense_date__lte=self.period_end,
        )

        categories = (
            expenses.values("category")
            .annotate(
                total=Coalesce(Sum("amount"), Decimal("0")),
                count=Count("id"),
            )
            .order_by("-total")[:limit]
        )

        return [
            {
                "category": item["category"],
                "total": float(item["total"]),
                "count": item["count"],
            }
            for item in categories
        ]

    def collect_period_comparison(self) -> dict:
        """Сравнивает текущий период с предыдущим периодом той же длины."""
        # Вычисляем длительность текущего периода
        period_duration = self.period_end - self.period_start

        # Предыдущий период: той же длины, сразу перед текущим
        prev_period_end = self.period_start
        prev_period_start = self.period_start - period_duration

        # Создаём сервис для предыдущего периода
        prev_service = MetricsService(
            organization=self.organization,
            period_start=prev_period_start,
            period_end=prev_period_end,
        )

        # Собираем метрики для обоих периодов
        current_sales = self.collect_sales_metrics()
        current_finance = self.collect_finance_metrics()

        prev_sales = prev_service.collect_sales_metrics()
        prev_finance = prev_service.collect_finance_metrics()

        # Вычисляем изменения в процентах
        changes = {
            "revenue_change": self._calculate_percentage_change(
                current_finance["total_revenue"],
                prev_finance["total_revenue"],
            ),
            "expenses_change": self._calculate_percentage_change(
                current_finance["total_expenses"],
                prev_finance["total_expenses"],
            ),
            "profit_change": self._calculate_percentage_change(
                current_finance["net_profit"],
                prev_finance["net_profit"],
            ),
            "orders_change": self._calculate_percentage_change(
                current_sales["total_orders"],
                prev_sales["total_orders"],
            ),
        }

        return {
            "current_period": {
                "start": self.period_start.isoformat(),
                "end": self.period_end.isoformat(),
                "revenue": current_finance["total_revenue"],
                "expenses": current_finance["total_expenses"],
                "profit": current_finance["net_profit"],
                "orders_count": current_sales["total_orders"],
            },
            "previous_period": {
                "start": prev_period_start.isoformat(),
                "end": prev_period_end.isoformat(),
                "revenue": prev_finance["total_revenue"],
                "expenses": prev_finance["total_expenses"],
                "profit": prev_finance["net_profit"],
                "orders_count": prev_sales["total_orders"],
            },
            "changes": changes,
        }

    @staticmethod
    def _calculate_percentage_change(current: float, previous: float) -> float | None:
        """Вычисляет процентное изменение."""
        if previous == 0:
            if current == 0:
                return 0.0
            return None  # Невозможно вычислить, если предыдущее значение 0
        return round(((current - previous) / abs(previous)) * 100, 2)
