from django.contrib import admin

from business_data.models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "organization",
        "amount",
        "currency",
        "status",
        "order_date",
    )
    list_filter = ("status", "currency", "organization")
    search_fields = ("description",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "order_date"
