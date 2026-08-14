from django.contrib import admin

from reports.models import Report


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
