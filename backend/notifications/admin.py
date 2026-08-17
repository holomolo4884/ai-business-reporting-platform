from django.contrib import admin

from notifications.models import NotificationLog


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    """Админка для логов уведомлений."""

    list_display = [
        "id",
        "channel",
        "recipient",
        "status",
        "attempts",
        "user",
        "created_at",
        "sent_at",
    ]
    list_filter = ["status", "channel", "created_at"]
    search_fields = ["recipient", "subject", "message"]
    readonly_fields = [
        "id",
        "notification_id",
        "created_at",
        "sent_at",
        "attempts",
    ]
    raw_id_fields = ["user", "report"]
    ordering = ["-created_at"]

    def has_add_permission(self, request):
        """Запрещаем ручное создание логов."""
        return False
