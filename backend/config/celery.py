import os

from celery import Celery
from celery.schedules import crontab

# Устанавливаем модуль настроек Django по умолчанию
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")

# Создаём Celery приложение
app = Celery("business_reporting")

# Загружаем настройки из Django settings с префиксом CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Ищем файл tasks.py в каждом приложении из INSTALLED_APPS
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Тестовая задача для проверки работы Celery."""
    print(f"Запрос: {self.request!r}")


# Периодические задачи для Celery Beat
app.conf.beat_schedule = {
    "check-scheduled-reports-every-minute": {
        "task": "reports.tasks.check_and_run_scheduled_reports_task",
        "schedule": crontab(minute="*/1"),  # Каждую минуту
        "options": {
            "expires": 60,  # Если задача не запустилась за 60 секунд — пропускаем
        },
    },
}

# Используем UTC для времени в Beat
app.conf.timezone = "UTC"
