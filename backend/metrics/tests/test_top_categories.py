import pytest


@pytest.mark.django_db
class TestTopCategories:
    """Тесты топ категорий расходов."""

    def test_top_categories_order(self, metrics_service, sample_orders, sample_expenses):
        """Проверяет, что категории отсортированы по сумме."""
        categories = metrics_service.collect_top_categories()

        # Ожидаемый порядок: salary (5000), rent (1000), marketing (800), software (200)
        assert len(categories) == 4
        assert categories[0]["category"] == "salary"
        assert categories[0]["total"] == 5000.0
        assert categories[1]["category"] == "rent"
        assert categories[1]["total"] == 1000.0
        assert categories[2]["category"] == "marketing"
        assert categories[2]["total"] == 800.0
        assert categories[3]["category"] == "software"
        assert categories[3]["total"] == 200.0

    def test_top_categories_count(self, metrics_service, sample_orders, sample_expenses):
        """Проверяет количество расходов в каждой категории."""
        categories = metrics_service.collect_top_categories()

        # marketing имеет 2 расхода
        marketing = next(c for c in categories if c["category"] == "marketing")
        assert marketing["count"] == 2

        # salary имеет 1 расход
        salary = next(c for c in categories if c["category"] == "salary")
        assert salary["count"] == 1

    def test_top_categories_limit(self, metrics_service, sample_orders, sample_expenses):
        """Проверяет ограничение количества категорий."""
        categories = metrics_service.collect_top_categories(limit=2)

        assert len(categories) == 2
        assert categories[0]["category"] == "salary"
        assert categories[1]["category"] == "rent"

    def test_empty_period(self, metrics_service):
        """Проверяет топ категории за период без данных."""
        categories = metrics_service.collect_top_categories()

        assert categories == []
