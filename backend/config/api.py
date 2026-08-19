from datetime import UTC, datetime

import django
from django.db import connection
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response


class HealthCheckSerializer(serializers.Serializer):
    """Сериализатор для health check endpoint."""

    status = serializers.ChoiceField(
        choices=["ok", "degraded"],
        help_text="Общий статус сервиса",
    )
    service = serializers.CharField(
        help_text="Название сервиса",
    )
    version = serializers.CharField(
        help_text="Версия сервиса",
    )
    django_version = serializers.CharField(
        help_text="Версия Django",
    )
    database = serializers.ChoiceField(
        choices=["connected", "disconnected"],
        help_text="Статус подключения к БД",
    )
    timestamp = serializers.DateTimeField(
        help_text="Время проверки",
    )


@extend_schema(
    tags=["Health"],
    summary="Health check",
    description=(
        "Проверяет работоспособность API и его зависимостей.\n\n"
        "Возвращает статус `ok`, если все компоненты работают, "
        "или `degraded` при проблемах с БД."
    ),
    responses={
        200: HealthCheckSerializer,
    },
    examples=[
        OpenApiExample(
            "Healthy",
            value={
                "status": "ok",
                "service": "ai-business-reporting-platform",
                "version": "1.0.0",
                "django_version": "5.2.17",
                "database": "connected",
                "timestamp": "2026-08-19T19:00:00Z",
            },
        ),
        OpenApiExample(
            "Degraded",
            value={
                "status": "degraded",
                "service": "ai-business-reporting-platform",
                "version": "1.0.0",
                "django_version": "5.2.17",
                "database": "disconnected",
                "timestamp": "2026-08-19T19:00:00Z",
            },
        ),
    ],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request: Request) -> Response:
    """Health check endpoint."""
    database_status = _check_database()

    status = "ok" if database_status else "degraded"

    data = {
        "status": status,
        "service": "ai-business-reporting-platform",
        "version": "1.0.0",
        "django_version": django.get_version(),
        "database": "connected" if database_status else "disconnected",
        "timestamp": datetime.now(UTC).isoformat(),
    }

    return Response(data)


def _check_database() -> bool:
    """Проверяет подключение к базе данных."""
    try:
        connection.ensure_connection()
        return True
    except Exception:
        return False
