import json
import logging
import time

from ai.exceptions import AIError
from ai.prompts import get_prompt_template
from ai.providers import get_ai_provider
from reports.models import Report

logger = logging.getLogger(__name__)


class AIClient:
    """
    Клиент для генерации отчётов с помощью AI.

    Использует выбранный AI провайдер для генерации текста отчёта
    на основе собранных бизнес-метрик.
    """

    def __init__(self):
        self.provider = get_ai_provider()

    def generate_report(self, report: Report) -> dict:
        """
        Генерирует отчёт для заданного Report.

        Args:
            report: Модель Report с заполненными метриками.

        Returns:
            Словарь с полями: summary, insights, recommendations, generated_text.
        """
        logger.info("Генерация отчёта #%s через AI", report.id)

        # Формируем промпт из метрик
        prompt = self._build_prompt(report)

        # Вызываем AI провайдер
        start_time = time.time()
        try:
            response = self.provider.generate_report(
                prompt=prompt,
                report_type=report.report_type,
            )
        except AIError:
            raise
        except Exception as exc:
            raise AIError(f"Ошибка при вызове AI: {exc}") from exc

        elapsed = time.time() - start_time
        logger.info(
            "AI ответ получен за %.2f секунд для отчёта #%s",
            elapsed,
            report.id,
        )

        return response

    def _build_prompt(self, report: Report) -> str:
        """Формирует промпт из метрик отчёта."""
        template = get_prompt_template(report.report_type)
        metrics = report.metrics or {}

        # Извлекаем данные из метрик
        period = metrics.get("period", {})
        sales = metrics.get("sales", {})
        finance = metrics.get("finance", {})
        top_categories = metrics.get("top_expense_categories", [])

        # Форматируем топ категорий
        categories_text = (
            "\n".join(
                f"- {cat['category']}: {cat['total']} ({cat['count']} шт)" for cat in top_categories
            )
            or "Нет данных"
        )

        # Заполняем шаблон
        try:
            prompt = template.format(
                period_start=period.get("start", "N/A"),
                period_end=period.get("end", "N/A"),
                period_days=report.period_days,
                total_orders=sales.get("total_orders", 0),
                paid_orders=sales.get("paid_orders", 0),
                pending_orders=sales.get("pending_orders", 0),
                cancelled_orders=sales.get("cancelled_orders", 0),
                refunded_orders=sales.get("refunded_orders", 0),
                total_revenue=finance.get("total_revenue", 0),
                average_order_value=sales.get("average_order_value", 0),
                total_expenses=finance.get("total_expenses", 0),
                net_profit=finance.get("net_profit", 0),
                profit_margin=finance.get("profit_margin", 0),
                is_profitable="Да" if finance.get("is_profitable") else "Нет",
                currency="USD",
                top_categories=categories_text,
                metrics_json=json.dumps(metrics, indent=2, ensure_ascii=False),
            )
        except KeyError as err:
            logger.error("Не хватает данных для промпта: %s", err)
            prompt = f"Сгенерируй отчёт на основе данных: {json.dumps(metrics)}"

        return prompt
