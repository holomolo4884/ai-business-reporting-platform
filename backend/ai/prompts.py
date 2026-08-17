SALES_REPORT_PROMPT = """
Ты — бизнес-аналитик. Проанализируй следующие бизнес-метрики и составь отчёт.

## Период
С {period_start} по {period_end} ({period_days} дней)

## Метрики продаж
- Всего заказов: {total_orders}
- Оплачено: {paid_orders}
- В ожидании: {pending_orders}
- Отменено: {cancelled_orders}
- Возвращено: {refunded_orders}
- Общая выручка: {total_revenue} {currency}
- Средний чек: {average_order_value} {currency}

## Финансовые метрики
- Выручка: {total_revenue} {currency}
- Расходы: {total_expenses} {currency}
- Чистая прибыль: {net_profit} {currency}
- Маржа прибыли: {profit_margin}%
- Прибыльно: {is_profitable}

## Топ категорий расходов
{top_categories}

## Задача
Составь структурированный отчёт на русском языке.

Ответ ДОЛЖЕН быть в формате JSON со следующей структурой:
{{
  "summary": "Краткое резюме отчёта (2-3 предложения)",
  "insights": [
    {{
      "title": "Заголовок инсайта",
      "description": "Описание",
      "importance": "high|medium|low"
    }}
  ],
  "recommendations": [
    {{
      "title": "Заголовок рекомендации",
      "description": "Описание",
      "expected_impact": "Ожидаемый эффект"
    }}
  ],
  "generated_text": "Полный текст отчёта (3-5 абзацев)"
}}

ВАЖНО: Верни ТОЛЬКО валидный JSON объект, начинающийся с '{{' и заканчивающийся '}}'.
НЕ оборачивай в markdown блоки. НЕ добавляй пояснений до или после JSON.
""".strip()


FINANCE_REPORT_PROMPT = """
Ты — финансовый аналитик. Проанализируй финансовые показатели и составь отчёт.

## Период
С {period_start} по {period_end} ({period_days} дней)

## Финансовые метрики
- Выручка: {total_revenue} {currency}
- Расходы: {total_expenses} {currency}
- Чистая прибыль: {net_profit} {currency}
- Маржа прибыли: {profit_margin}%

## Топ категорий расходов
{top_categories}

## Задача
Составь финансовый отчёт на русском языке.

Ответ ДОЛЖЕН быть в формате JSON со следующей структурой:
{{
  "summary": "Краткое резюме",
  "insights": [...],
  "recommendations": [...],
  "generated_text": "Полный текст отчёта"
}}

ВАЖНО: Верни ТОЛЬКО валидный JSON объект, начинающийся с '{{' и заканчивающийся '}}'.
НЕ оборачивай в markdown блоки. НЕ добавляй пояснений до или после JSON.
""".strip()


CUSTOM_REPORT_PROMPT = """
Ты — бизнес-аналитик. Проанализируй метрики и составь кастомный отчёт.

## Период
С {period_start} по {period_end}

## Метрики
{metrics_json}

## Задача
Составь отчёт на русском языке.

Ответ ДОЛЖЕН быть в формате JSON со структурой:
{{
  "summary": "...",
  "insights": [...],
  "recommendations": [...],
  "generated_text": "..."
}}

ВАЖНО: Верни ТОЛЬКО валидный JSON объект, начинающийся с '{{' и заканчивающийся '}}'.
НЕ оборачивай в markdown блоки. НЕ добавляй пояснений до или после JSON.
""".strip()


def get_prompt_template(report_type: str) -> str:
    """Возвращает шаблон промпта по типу отчёта."""
    from reports.models import Report  # noqa: E402

    templates = {
        Report.ReportType.SALES: SALES_REPORT_PROMPT,
        Report.ReportType.FINANCE: FINANCE_REPORT_PROMPT,
        Report.ReportType.CUSTOM: CUSTOM_REPORT_PROMPT,
    }
    return templates.get(report_type, CUSTOM_REPORT_PROMPT)
