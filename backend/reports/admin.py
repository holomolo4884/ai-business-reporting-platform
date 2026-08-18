from django.contrib import admin

from reports.models import Report, ReportSchedule


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "organization",
        "report_type",
        "status",
        "period_start",
        "period_end",
        "created_by",
        "created_at",
    )
    list_filter = ("report_type", "status", "organization")
    search_fields = ("organization__name",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "completed_at",
        "metrics",
        "ai_response",
        "generated_text",
        "error",
    )
    date_hierarchy = "created_at"
    fieldsets = (
        (
            None,
            {
                "fields": ("organization", "created_by", "report_type", "status"),
            },
        ),
        (
            "Период",
            {
                "fields": ("period_start", "period_end"),
            },
        ),
        (
            "Данные",
            {
                "fields": ("metrics", "ai_response", "generated_text", "error"),
            },
        ),
        (
            "Файл",
            {
                "fields": ("pdf_file",),
            },
        ),
        (
            "Временные метки",
            {
                "fields": ("created_at", "updated_at", "completed_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    """Админка для расписаний отчётов"""

    list_display = [
        "id",
        "organization",
        "report_type",
        "frequency",
        "is_active",
        "next_run_at",
        "last_run_at",
    ]
    list_filter = ["frequency", "is_active", "report_type", "created_at"]
    search_fields = ["organization_name"]
    readonly_fields = ["id", "created_at", "updated_at", "next_run_at", "last_run_at"]
    raw_id_fields = ["organization", "created_by"]
    ordering = ["-created_at"]

    fieldsets = (
        (
            "Основаная информация",
            {
                "fields": ("organization", "report_type", "created_by", "is_active"),
            },
        ),
        (
            "Расписание",
            {
                "fields": (
                    "frequency",
                    "run_at_hour",
                    "run_at_minute",
                    "run_day_of_week",
                    "run_day_of_month",
                ),
            },
        ),
        (
            "Состояние",
            {
                "fields": ("last_run_at", "next_run_at"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
