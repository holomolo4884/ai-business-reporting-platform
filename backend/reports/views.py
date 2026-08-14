from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from organizations.models import Organization
from reports.models import Report
from reports.serializers import (
    ReportGenerateSerializer,
    ReportSerializer,
)


class ReportGenerateView(APIView):
    """Endpoint для генерации отчёта."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = ReportGenerateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        organization_id = serializer.validated_data["organization_id"]
        organization = Organization.objects.get(id=organization_id)

        # Создаём отчёт со статусом pending
        report = Report.objects.create(
            organization=organization,
            created_by=request.user,
            report_type=serializer.validated_data["report_type"],
            status=Report.Status.PENDING,
            period_start=serializer.validated_data["period_start"],
            period_end=serializer.validated_data["period_end"],
        )

        # TODO: Запустить фоновую задачу генерации (Celery)
        # from reports.tasks import generate_report_task
        # generate_report_task.delay(report.id)

        return Response(
            {
                "message": "Отчёт поставлен в очередь на генерацию.",
                "report": ReportSerializer(report).data,
            },
            status=status.HTTP_202_ACCEPTED,
        )
