import os

from celery import Celery

# Устанавливаем модуль настроек Django по умолчанию
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")

# Создаём Celery приложение
app = Celery("business_reporting")

# Загружаем настройки из Django settings с префиксом CELERY_
# Например: CELERY_BROKER_URL, CELERY_RESULT_BACKEND и т.д.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Автоматически обнаруживаем задачи во всех приложениях Django
# Ищем файл tasks.py в каждом приложении из INSTALLED_APPS
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Тестовая задача для проверки работы Celery."""
    print(f"Запрос: {self.request!r}")
