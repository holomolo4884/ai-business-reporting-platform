from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from organizations.models import Organization, OrganizationMember
from reports.filters import ReportFilter
from reports.models import Report, ReportSchedule
from reports.serializers import (
    ReportGenerateSerializer,
    ReportListSerializer,
    ReportScheduleSerializer,
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


class ReportDetailView(RetrieveAPIView):
    """Endpoint для получения деталей отчёта."""

    permission_classes = [IsAuthenticated]
    serializer_class = ReportSerializer
    lookup_url_kwarg = "report_id"  # Параметр из URL: reports/<int:report_id>/

    def get_queryset(self):
        # Пользователь видит только отчёты своих организаций
        return (
            Report.objects.filter(organization__members__user=self.request.user)
            .distinct()
            .select_related("organization", "created_by")
        )


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


class ReportScheduleListCreateView(APIView):
    """
    Список расписаний организации и создание нового.

    GET: Получить список расписаний (все участники организации)
    POST: Создать расписание (только owner/admin)
    """

    permission_classes = [IsAuthenticated]

    def get_organization_or_404(self, organization_id: int, user) -> Organization:
        """Получает организацию или 404."""
        org = get_object_or_404(Organization, id=organization_id)
        if not OrganizationMember.objects.filter(organization=org, user=user).exists():
            raise PermissionDenied("У вас нет доступа к этой организации.")
        return org

    def get(self, request: Request, organization_id: int) -> Response:
        """Список расписаний организации."""
        org = self.get_organization_or_404(organization_id, request.user)

        schedules = ReportSchedule.objects.filter(organization=org).select_related(
            "organization", "created_by"
        )

        serializer = ReportScheduleSerializer(schedules, many=True)
        return Response(serializer.data)

    def post(self, request: Request, organization_id: int) -> Response:
        """Создать расписание."""
        org = self.get_organization_or_404(organization_id, request.user)

        # Проверяем роль (только owner/admin)
        membership = OrganizationMember.objects.get(organization=org, user=request.user)
        if membership.role not in [
            OrganizationMember.Role.OWNER,
            OrganizationMember.Role.ADMIN,
        ]:
            raise PermissionDenied("Только владельцы и администраторы могут создавать расписания.")

        serializer = ReportScheduleSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        # Привязываем организацию
        serializer.save(organization=org)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ReportScheduleDetailView(APIView):
    """
    Детали расписания.

    GET: Получить расписание
    PATCH: Обновить (только owner/admin)
    DELETE: Удалить (только owner/admin)
    """

    permission_classes = [IsAuthenticated]

    def get_object_or_404_with_permission(
        self, schedule_id: int, user, require_admin: bool = False
    ) -> ReportSchedule:
        """Получает расписание с проверкой доступа."""
        schedule = get_object_or_404(
            ReportSchedule.objects.select_related("organization", "created_by"),
            id=schedule_id,
        )

        # Проверяем членство в организации
        try:
            membership = OrganizationMember.objects.get(
                organization=schedule.organization,
                user=user,
            )
        except OrganizationMember.DoesNotExist as err:
            raise PermissionDenied("У вас нет доступа к этому расписанию.") from err

        # Для изменений нужна роль owner/admin
        if require_admin and membership.role not in [
            OrganizationMember.Role.OWNER,
            OrganizationMember.Role.ADMIN,
        ]:
            raise PermissionDenied(
                "Только владельцы и администраторы могут изменять расписания."
            ) from None

        return schedule

    def get(self, request: Request, schedule_id: int) -> Response:
        """Получить расписание."""
        schedule = self.get_object_or_404_with_permission(schedule_id, request.user)
        serializer = ReportScheduleSerializer(schedule)
        return Response(serializer.data)

    def patch(self, request: Request, schedule_id: int) -> Response:
        """Обновить расписание."""
        schedule = self.get_object_or_404_with_permission(
            schedule_id, request.user, require_admin=True
        )

        serializer = ReportScheduleSerializer(
            schedule,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def delete(self, request: Request, schedule_id: int) -> Response:
        """Удалить расписание."""
        schedule = self.get_object_or_404_with_permission(
            schedule_id, request.user, require_admin=True
        )
        schedule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
