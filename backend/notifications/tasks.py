import logging
import time

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def sample_task(message: str = "Привет из Celery!") -> str:
    """Простая тестовая задача."""
    logger.info("Задача sample_task запущена: %s", message)
    time.sleep(2)  # Симулируем работу
    logger.info("Задача sample_task завершена")
    return f"Задача выполнена: {message}"


@shared_task
def add_numbers(x: int, y: int) -> int:
    """Задача для сложения чисел."""
    logger.info("Сложение: %s + %s", x, y)
    return x + y


@shared_task
def failing_task() -> None:
    """Задача, которая всегда падает (для тестирования ошибок)."""
    logger.info("Задача failing_task запущена")
    raise ValueError("Это тестовая ошибка!")
