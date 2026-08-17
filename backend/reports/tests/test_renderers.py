from datetime import timedelta

import pytest
from django.utils import timezone

from reports.models import Report
from reports.renderers import ReportRenderer


@pytest.fixture
def sales_report_for_render(db, test_user):
    """Отчёт с данными для рендеринга."""
    from organizations.models import Organization, OrganizationMember  # noqa: E402

    org = Organization.objects.create(
        name="Test Render Org",
        description="Org for render tests",
    )
    OrganizationMember.objects.create(
        organization=org,
        user=test_user,
        role=OrganizationMember.Role.OWNER,
    )

    now = timezone.now()
    report = Report.objects.create(
        organization=org,
        created_by=test_user,
        report_type=Report.ReportType.SALES,
        status=Report.Status.COMPLETED,
        period_start=now - timedelta(days=30),
        period_end=now,
        completed_at=now,
    )

    # Заполняем метрики
    report.metrics = {
        "period": {
            "start": (now - timedelta(days=30)).isoformat(),
            "end": now.isoformat(),
        },
        "sales": {
            "total_orders": 100,
            "paid_orders": 80,
            "pending_orders": 10,
            "cancelled_orders": 5,
            "refunded_orders": 5,
            "total_revenue": 50000.0,
            "average_order_value": 625.0,
        },
        "finance": {
            "total_revenue": 50000.0,
            "total_expenses": 30000.0,
            "net_profit": 20000.0,
            "profit_margin": 40.0,
            "expenses_count": 50,
            "is_profitable": True,
        },
        "top_expense_categories": [
            {"category": "salary", "total": 15000.0, "count": 10},
            {"category": "marketing", "total": 8000.0, "count": 5},
            {"category": "rent", "total": 5000.0, "count": 3},
        ],
    }

    # Заполняем AI ответ
    report.ai_response = {
        "summary": "Компания показала хорошие результаты за период.",
        "insights": [
            {
                "title": "Высокая конверсия",
                "description": "80% заказов оплачено.",
                "importance": "high",
            },
            {
                "title": "Стабильный рост",
                "description": "Выручка растёт.",
                "importance": "medium",
            },
        ],
        "recommendations": [
            {
                "title": "Увеличить маркетинг",
                "description": "Инвестировать в привлечение клиентов.",
                "expected_impact": "Рост выручки на 20%",
            },
        ],
        "generated_text": "Тестовый текст",
    }

    report.save()
    return report


@pytest.mark.django_db
class TestReportRenderer:
    """Тесты ReportRenderer."""

    def test_render_text_contains_header(self, sales_report_for_render):
        """Текст содержит заголовок."""
        renderer = ReportRenderer(sales_report_for_render)
        text = renderer.render_text()

        assert "# Отчёт о продажах" in text
        assert "Test Render Org" in text

    def test_render_text_contains_summary(self, sales_report_for_render):
        """Текст содержит резюме от AI."""
        renderer = ReportRenderer(sales_report_for_render)
        text = renderer.render_text()

        assert "## Резюме" in text
        assert "хорошие результаты" in text

    def test_render_text_contains_metrics(self, sales_report_for_render):
        """Текст содержит метрики."""
        renderer = ReportRenderer(sales_report_for_render)
        text = renderer.render_text()

        assert "$50,000.00" in text  # Выручка
        assert "$30,000.00" in text  # Расходы
        assert "$20,000.00" in text  # Прибыль

    def test_render_text_contains_insights(self, sales_report_for_render):
        """Текст содержит инсайты."""
        renderer = ReportRenderer(sales_report_for_render)
        text = renderer.render_text()

        assert "## Ключевые инсайты" in text
        assert "Высокая конверсия" in text
        assert "🔴" in text  # high importance

    def test_render_text_contains_recommendations(self, sales_report_for_render):
        """Текст содержит рекомендации."""
        renderer = ReportRenderer(sales_report_for_render)
        text = renderer.render_text()

        assert "## Рекомендации" in text
        assert "Увеличить маркетинг" in text
        assert "Рост выручки на 20%" in text

    def test_render_text_contains_footer(self, sales_report_for_render):
        """Текст содержит футер."""
        renderer = ReportRenderer(sales_report_for_render)
        text = renderer.render_text()

        assert "Отчёт сгенерирован автоматически" in text

    def test_render_text_with_empty_ai_response(self, sales_report_for_render):
        """Рендеринг без AI ответа не падает."""
        sales_report_for_render.ai_response = {}
        sales_report_for_render.save()

        renderer = ReportRenderer(sales_report_for_render)
        text = renderer.render_text()

        # Должен быть хотя бы заголовок и метрики
        assert "# Отчёт о продажах" in text
        assert len(text) > 0

    def test_render_text_with_empty_metrics(self, sales_report_for_render):
        """Рендеринг без метрик не падает."""
        sales_report_for_render.metrics = {}
        sales_report_for_render.save()

        renderer = ReportRenderer(sales_report_for_render)
        text = renderer.render_text()

        # Должен быть хотя бы заголовок и резюме
        assert "# Отчёт о продажах" in text
        assert len(text) > 0

    def test_render_html_returns_valid_html(self, sales_report_for_render):
        """HTML рендеринг возвращает валидный HTML."""
        renderer = ReportRenderer(sales_report_for_render)
        html = renderer.render_html()

        assert html.startswith("<!DOCTYPE html>")
        assert "<html" in html
        assert "</html>" in html
        assert "<head>" in html
        assert "<body>" in html

    def test_render_html_contains_organization(self, sales_report_for_render):
        """HTML содержит название организации."""
        renderer = ReportRenderer(sales_report_for_render)
        html = renderer.render_html()

        assert "Test Render Org" in html

    def test_render_html_contains_metrics(self, sales_report_for_render):
        """HTML содержит метрики."""
        renderer = ReportRenderer(sales_report_for_render)
        html = renderer.render_html()

        assert "50,000.00" in html or "50000" in html  # Выручка
        assert "30,000.00" in html or "30000" in html  # Расходы

    def test_render_html_contains_insights(self, sales_report_for_render):
        """HTML содержит инсайты."""
        renderer = ReportRenderer(sales_report_for_render)
        html = renderer.render_html()

        assert "Высокая конверсия" in html
        assert "insight" in html

    def test_render_html_contains_recommendations(self, sales_report_for_render):
        """HTML содержит рекомендации."""
        renderer = ReportRenderer(sales_report_for_render)
        html = renderer.render_html()

        assert "Увеличить маркетинг" in html
        assert "recommendation" in html

    def test_render_html_with_empty_data(self, sales_report_for_render):
        """HTML рендеринг работает с пустыми данными."""
        sales_report_for_render.ai_response = {}
        sales_report_for_render.metrics = {}
        sales_report_for_render.save()

        renderer = ReportRenderer(sales_report_for_render)
        html = renderer.render_html()

        # Должен быть валидный HTML
        assert html.startswith("<!DOCTYPE html>")
        assert "Test Render Org" in html
