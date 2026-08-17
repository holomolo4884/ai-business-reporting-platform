import logging

from reports.models import Report

logger = logging.getLogger(__name__)


class ReportRenderer:
    """
    Рендерер отчётов.

    Преобразует AI-ответ и метрики в читаемый текст и HTML.
    """

    def __init__(self, report: Report):
        self.report = report
        self.ai_response = report.ai_response or {}
        self.metrics = report.metrics or {}

    def render_text(self) -> str:
        """
        Формирует текстовый отчёт в markdown-стиле.

        Возвращает структурированный текст, который можно использовать
        как generated_text или основу для дальнейшей обработки.
        """
        sections = []

        # Заголовок
        sections.append(self._render_header())

        # Краткое резюме
        sections.append(self._render_summary())

        # Ключевые метрики
        sections.append(self._render_metrics_summary())

        # Инсайты
        sections.append(self._render_insights())

        # Рекомендации
        sections.append(self._render_recommendations())

        # Детальная статистика
        sections.append(self._render_detailed_stats())

        # Футер
        sections.append(self._render_footer())

        # Объединяем секции, фильтруя пустые
        return "\n\n".join(section for section in sections if section)

    def _render_header(self) -> str:
        """Заголовок отчёта с периодом."""
        report_type_display = {
            Report.ReportType.SALES: "Отчёт о продажах",
            Report.ReportType.FINANCE: "Финансовый отчёт",
            Report.ReportType.CUSTOM: "Бизнес-отчёт",
        }
        title = report_type_display.get(self.report.report_type, "Бизнес-отчёт")

        period_start = self.report.period_start.strftime("%d.%m.%Y")
        period_end = self.report.period_end.strftime("%d.%m.%Y")

        return (
            f"# {title}\n\n"
            f"**Организация:** {self.report.organization.name}\n"
            f"**Период:** {period_start} — {period_end} ({self.report.period_days} дней)"
        )

    def _render_summary(self) -> str:
        """Краткое резюме от AI."""
        summary = self.ai_response.get("summary")
        if not summary:
            return ""
        return f"## Резюме\n\n{summary}"

    def _render_metrics_summary(self) -> str:
        """Ключевые метрики одной строкой."""
        finance = self.metrics.get("finance", {})
        sales = self.metrics.get("sales", {})

        revenue = finance.get("total_revenue", 0)
        expenses = finance.get("total_expenses", 0)
        profit = finance.get("net_profit", 0)
        orders_count = sales.get("total_orders", 0)

        profit_sign = "+" if profit >= 0 else ""
        profit_emoji = "📈" if profit >= 0 else "📉"

        return (
            "## Ключевые показатели\n\n"
            f"- **Выручка:** ${revenue:,.2f}\n"
            f"- **Расходы:** ${expenses:,.2f}\n"
            f"- **Прибыль:** {profit_sign}${profit:,.2f} {profit_emoji}\n"
            f"- **Заказов:** {orders_count}"
        )

    def _render_insights(self) -> str:
        """Секция с инсайтами."""
        insights = self.ai_response.get("insights", [])
        if not insights:
            return ""

        lines = ["## Ключевые инсайты"]

        importance_emoji = {
            "high": "🔴",
            "medium": "🟡",
            "low": "🟢",
        }

        for insight in insights:
            title = insight.get("title", "")
            description = insight.get("description", "")
            importance = insight.get("importance", "medium")
            emoji = importance_emoji.get(importance, "⚪")

            lines.append(f"\n### {emoji} {title}\n\n{description}")

        return "\n".join(lines)

    def _render_recommendations(self) -> str:
        """Секция с рекомендациями."""
        recommendations = self.ai_response.get("recommendations", [])
        if not recommendations:
            return ""

        lines = ["## Рекомендации"]

        for i, rec in enumerate(recommendations, start=1):
            title = rec.get("title", "")
            description = rec.get("description", "")
            impact = rec.get("expected_impact", "")

            lines.append(f"\n### {i}. {title}\n\n{description}")
            if impact:
                lines.append(f"\n*Ожидаемый эффект: {impact}*")

        return "\n".join(lines)

    def _render_detailed_stats(self) -> str:
        """Детальная статистика из метрик."""
        sales = self.metrics.get("sales", {})
        finance = self.metrics.get("finance", {})
        top_categories = self.metrics.get("top_expense_categories", [])

        lines = ["## Детальная статистика"]

        # Статистика продаж
        if sales:
            lines.append("\n### Продажи\n")
            lines.append(f"- Всего заказов: {sales.get('total_orders', 0)}")
            lines.append(f"- Оплачено: {sales.get('paid_orders', 0)}")
            lines.append(f"- В ожидании: {sales.get('pending_orders', 0)}")
            lines.append(f"- Отменено: {sales.get('cancelled_orders', 0)}")
            lines.append(f"- Возвращено: {sales.get('refunded_orders', 0)}")
            lines.append(f"- Средний чек: ${sales.get('average_order_value', 0):,.2f}")

        # Финансы
        if finance:
            lines.append("\n### Финансы\n")
            margin = finance.get("profit_margin", 0)
            lines.append(f"- Маржа прибыли: {margin}%")
            lines.append(f"- Количество расходных операций: {finance.get('expenses_count', 0)}")

        # Топ категорий расходов
        if top_categories:
            lines.append("\n### Топ категорий расходов\n")
            for cat in top_categories:
                category_name = cat.get("category", "").replace("_", " ").title()
                total = cat.get("total", 0)
                count = cat.get("count", 0)
                lines.append(f"- **{category_name}**: ${total:,.2f} ({count} операций)")

        return "\n".join(lines)

    def _render_footer(self) -> str:
        """Футер отчёта."""
        completed_at = self.report.completed_at
        if completed_at:
            generated_time = completed_at.strftime("%d.%m.%Y %H:%M:%S")
        else:
            generated_time = "в процессе генерации"

        return "---\n\n" f"*Отчёт сгенерирован автоматически с помощью AI " f"{generated_time}*"
