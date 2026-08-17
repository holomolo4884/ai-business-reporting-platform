from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from organizations.models import Organization, OrganizationMember
from reports.filters import ReportFilter
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

        # Запускаем фоновую задачу генерации
        from reports.tasks import generate_report_task  # noqa: E402

        generate_report_task.delay(report.id)

        return Response(
            {
                "message": "Отчёт поставлен в очередь на генерацию.",
                "report": ReportSerializer(report).data,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class ReportListView(ListAPIView):
    """Endpoint для получения списка отчётов с пагинацией."""

    permission_classes = [IsAuthenticated]
    serializer_class = ReportListSerializer
    filterset_class = ReportFilter

    def get_queryset(self):
        # Пользователь видит только отчёты своих организаций
        return (
            Report.objects.filter(organization__members__user=self.request.user)
            .distinct()
            .select_related("organization", "created_by")
            .order_by("-created_at")
        )


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


class ReportRegenerateView(APIView):
    """Endpoint для повторной генерации отчёта."""

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

        return report

    def post(self, request: Request, report_id: int) -> Response:
        report = self.get_object(report_id, request.user)

        # Нельзя перезапускать отчёт, который сейчас в процессе генерации
        if report.is_in_progress:
            return Response(
                {
                    "detail": (
                        "Отчёт уже находится в процессе генерации. "
                        "Дождитесь завершения или попробуйте позже."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        # Сбрасываем все данные предыдущей генерации
        report.status = Report.Status.PENDING
        report.metrics = {}
        report.ai_response = {}
        report.generated_text = ""
        report.error = ""
        report.completed_at = None

        # Удаляем предыдущий PDF-файл, если он есть
        if report.pdf_file:
            report.pdf_file.delete(save=False)
            report.pdf_file = None

        report.save()

        # Запускаем фоновую задачу генерации
        from reports.tasks import generate_report_task  # noqa: E402

        generate_report_task.delay(report.id)

        return Response(
            {
                "message": "Отчёт поставлен в очередь на повторную генерацию.",
                "report": ReportSerializer(report).data,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class ReportDownloadView(APIView):
    """Endpoint для скачивания PDF файла отчёта."""

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

        return report

    def get(self, request: Request, report_id: int) -> Response | FileResponse:
        report = self.get_object(report_id, request.user)

        # Проверяем, что отчёт завершён
        if not report.is_completed:
            return Response(
                {
                    "detail": (
                        "Отчёт ещё не завершён. " f"Текущий статус: {report.get_status_display()}"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Проверяем, что PDF файл существует
        if not report.pdf_file:
            return Response(
                {"detail": "PDF файл отчёта ещё не создан."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Проверяем, что файл физически существует на диске
        if not report.pdf_file.storage.exists(report.pdf_file.name):
            return Response(
                {"detail": "PDF файл не найден на сервере."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Возвращаем файл как attachment (скачивание)
        response = FileResponse(
            report.pdf_file.open("rb"),
            content_type="application/pdf",
            as_attachment=True,
            filename=f"report_{report.id}.pdf",
        )
        return response
