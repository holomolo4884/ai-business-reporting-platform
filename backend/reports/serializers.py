from django.utils import timezone
from rest_framework import serializers

from organizations.models import Organization, OrganizationMember
from reports.models import Report, ReportSchedule


class ReportGenerateSerializer(serializers.Serializer):
    """Serializer для запроса генерации отчёта."""

    organization_id = serializers.IntegerField()
    report_type = serializers.ChoiceField(
        choices=Report.ReportType.choices,
        default=Report.ReportType.SALES,
    )
    period_start = serializers.DateTimeField()
    period_end = serializers.DateTimeField()

    def validate_organization_id(self, value):
        """Проверяем, что организация существует и пользователь является участником."""
        request = self.context.get("request")

        try:
            organization = Organization.objects.get(id=value)
        except Organization.DoesNotExist as err:
            raise serializers.ValidationError("Организация не найдена.") from err

        if (
            request
            and request.user.is_authenticated
            and not OrganizationMember.objects.filter(
                organization=organization,
                user=request.user,
            ).exists()
        ):
            raise serializers.ValidationError("Вы не являетесь участником этой организации.")

        return value

    def validate(self, data):
        """Валидация периода."""
        period_start = data.get("period_start")
        period_end = data.get("period_end")

        if not period_start or not period_end:
            return data

        # period_start должен быть раньше period_end
        if period_start >= period_end:
            raise serializers.ValidationError(
                {"period_start": "Дата начала должна быть раньше даты окончания."}
            )

        # Период не должен быть в будущем
        now = timezone.now()
        if period_end > now:
            raise serializers.ValidationError(
                {"period_end": "Дата окончания не может быть в будущем."}
            )

        # Период не должен быть больше 365 дней
        max_period_days = 365
        period_days = (period_end - period_start).days
        if period_days > max_period_days:
            raise serializers.ValidationError(
                {"period_start": f"Период не может быть больше {max_period_days} дней."}
            )

        # Период не должен быть меньше 1 дня
        if period_days < 1:
            raise serializers.ValidationError(
                {"period_start": "Период должен быть не менее 1 дня."}
            )

        return data


class ReportSerializer(serializers.ModelSerializer):
    """Serializer для получения данных отчёта."""

    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
    )
    created_by_email = serializers.CharField(
        source="created_by.email",
        read_only=True,
    )
    period_days = serializers.IntegerField(read_only=True)

    class Meta:
        model = Report
        fields = (
            "id",
            "organization",
            "organization_name",
            "created_by",
            "created_by_email",
            "report_type",
            "status",
            "period_start",
            "period_end",
            "period_days",
            "metrics",
            "generated_text",
            "error",
            "pdf_file",
            "created_at",
            "updated_at",
            "completed_at",
        )
        read_only_fields = fields


class ReportListSerializer(serializers.ModelSerializer):
    """Serializer для списка отчётов (без больших полей)."""

    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
    )

    class Meta:
        model = Report
        fields = (
            "id",
            "organization",
            "organization_name",
            "report_type",
            "status",
            "period_start",
            "period_end",
            "created_at",
            "completed_at",
        )
        read_only_fields = fields


class ReportScheduleSerializer(serializers.ModelSerializer):
    """Сериализатор для расписаний отчётов."""

    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
    )
    created_by_email = serializers.CharField(
        source="created_by.email",
        read_only=True,
    )
    frequency_display = serializers.CharField(
        source="get_frequency_display",
        read_only=True,
    )
    report_type_display = serializers.CharField(
        source="get_report_type_display",
        read_only=True,
    )

    class Meta:
        model = ReportSchedule
        fields = (
            "id",
            "organization",
            "organization_name",
            "report_type",
            "report_type_display",
            "frequency",
            "frequency_display",
            "run_at_hour",
            "run_at_minute",
            "run_day_of_week",
            "run_day_of_month",
            "is_active",
            "last_run_at",
            "next_run_at",
            "created_by",
            "created_by_email",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "organization",
            "created_by",
            "created_at",
            "updated_at",
            "last_run_at",
        )

    def validate(self, attrs: dict) -> dict:
        """Проверяет согласованность полей расписания."""
        frequency = attrs.get("frequency", getattr(self.instance, "frequency", None))

        if frequency == ReportSchedule.Frequency.WEEKLY:
            # Для weekly проверяем день недели
            day_of_week = attrs.get(
                "run_day_of_week",
                getattr(self.instance, "run_day_of_week", None),
            )
            if day_of_week is not None and not (0 <= day_of_week <= 6):
                raise serializers.ValidationError(
                    {"run_day_of_week": "День недели должен быть от 0 до 6"}
                )

        if frequency == ReportSchedule.Frequency.MONTHLY:
            # Для monthly проверяем день месяца
            day_of_month = attrs.get(
                "run_day_of_month",
                getattr(self.instance, "run_day_of_month", None),
            )
            if day_of_month is not None and not (1 <= day_of_month <= 28):
                raise serializers.ValidationError(
                    {"run_day_of_month": "День месяца должен быть от 1 до 28"}
                )

        return attrs

    def create(self, validated_data: dict) -> ReportSchedule:
        """Создаёт расписание и устанавливает created_by."""
        from django.db import IntegrityError

        user = self.context["request"].user
        validated_data["created_by"] = user

        try:
            return super().create(validated_data)
        except IntegrityError as exc:
            raise serializers.ValidationError(
                {
                    "detail": (
                        "Расписание с такими параметрами уже существует для данной организации."
                    )
                }
            ) from exc
