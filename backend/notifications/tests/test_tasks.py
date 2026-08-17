import pytest

from notifications.tasks import add_numbers, failing_task, sample_task


@pytest.mark.django_db
class TestSampleTask:
    """Тесты для sample_task."""

    def test_sample_task_with_default_message(self):
        """Проверяет выполнение задачи с сообщением по умолчанию."""
        # Вызываем задачу — в тестах она выполняется синхронно
        result = sample_task.delay()

        # Проверяем статус — должен быть SUCCESS сразу
        assert result.status == "SUCCESS"

        # Проверяем результат
        assert result.result == "Задача выполнена: Привет из Celery!"

    def test_sample_task_with_custom_message(self):
        """Проверяет выполнение задачи с кастомным сообщением."""
        result = sample_task.delay("Кастомное сообщение")

        assert result.status == "SUCCESS"
        assert result.result == "Задача выполнена: Кастомное сообщение"

    def test_sample_task_apply_sync(self):
        """Проверяет прямой вызов задачи (без .delay())."""
        # Можно вызывать задачу напрямую как функцию
        output = sample_task("Прямой вызов")

        assert output == "Задача выполнена: Прямой вызов"


@pytest.mark.django_db
class TestAddNumbersTask:
    """Тесты для add_numbers."""

    def test_add_positive_numbers(self):
        """Проверяет сложение положительных чисел."""
        result = add_numbers.delay(5, 3)

        assert result.status == "SUCCESS"
        assert result.result == 8

    def test_add_negative_numbers(self):
        """Проверяет сложение с отрицательными числами."""
        result = add_numbers.delay(-5, 3)

        assert result.status == "SUCCESS"
        assert result.result == -2

    def test_add_zeros(self):
        """Проверяет сложение нулей."""
        result = add_numbers.delay(0, 0)

        assert result.status == "SUCCESS"
        assert result.result == 0


@pytest.mark.django_db
class TestFailingTask:
    """Тесты для failing_task."""

    def test_failing_task_raises_exception(self):
        """Проверяет, что ошибка из задачи пробрасывается в тест."""
        # В тестах с EAGER_PROPAGATES исключение пробрасывается сразу
        with pytest.raises(ValueError) as exc_info:
            failing_task.delay()

        assert "тестовая ошибка" in str(exc_info.value)

    def test_failing_task_status_is_failure(self):
        """Проверяет статус задачи после ошибки."""
        # try:
        #     failing_task.delay()
        # except ValueError:
        #     pass

        # Можно также проверить статус через .get()
        result = failing_task.apply(throw=False)
        assert result.status == "FAILURE"
