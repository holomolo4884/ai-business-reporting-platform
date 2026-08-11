from django.contrib import admin

from organizations.models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")
