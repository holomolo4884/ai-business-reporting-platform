from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from organizations.models import Organization, OrganizationMember
from reports.models import Report
from reports.serializers import (
    ReportGenerateSerializer,
    ReportListSerializer,
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


class ReportListView(APIView):
    """Endpoint для получения списка отчётов."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        # Пользователь видит только отчёты своих организаций
        reports = (
            Report.objects.filter(organization__members__user=request.user)
            .distinct()
            .select_related("organization", "created_by")
            .order_by("-created_at")
        )

        serializer = ReportListSerializer(reports, many=True)
        return Response(serializer.data)


class ReportDetailView(APIView):
    """Endpoint для получения деталей отчёта."""

    permission_classes = [IsAuthenticated]

    def get_object(self, report_id: int, user) -> Report:
        """Получает отчёт с проверкой прав доступа."""
        report = get_object_or_404(
            Report.objects.select_related("organization", "created_by"),
            id=report_id,
        )

        # Проверяем, что пользователь является участником организации
        if not OrganizationMember.objects.filter(
            organization=report.organization,
            user=user,
        ).exists():
            raise PermissionDenied("У вас нет доступа к этому отчёту.")

    def get(self, request: Request, report_id: int) -> Response:
        report = self.get_object(report_id, request.user)
        serializer = ReportSerializer(report)
        return Response(serializer.data)
