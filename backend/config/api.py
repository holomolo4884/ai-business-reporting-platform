from datetime import UTC, datetime

import django
from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request: Request) -> Response:
    database_status = _check_database()

    status = "ok" if database_status else "degraded"

    return Response(
        {
            "status": status,
            "service": "ai-business-reporting-platform",
            "version": "1.0.0",
            "django_version": django.get_version(),
            "database": "connected" if database_status else "disconnected",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )


def _check_database() -> bool:
    try:
        connection.ensure_connection()
        return True
    except Exception:
        return False
