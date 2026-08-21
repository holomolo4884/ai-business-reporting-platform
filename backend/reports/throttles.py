from rest_framework.throttling import UserRateThrottle


class ReportGenerateThrottle(UserRateThrottle):
    """
    Rate limit для генерации отчётов.

    Генерация отчёта — дорогая операция (AI вызов, Celery задача).
    Ограничиваем: не более 10 генераций в час на пользователя.
    """

    scope = "report_generate"
