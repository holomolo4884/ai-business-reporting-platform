from rest_framework.permissions import BasePermission

from organizations.models import OrganizationMember


class IsOrganizationMember(BasePermission):
    """Разрешает доступ только участникам организации."""

    def has_object_permission(self, request, view, obj):
        return OrganizationMember.objects.filter(
            organization=obj,
            user=request.user,
        ).exists()


class IsOrganizationOwner(BasePermission):
    """Разрешает доступ только владельцу организации."""

    def has_object_permission(self, request, view, obj):
        return OrganizationMember.objects.filter(
            organization=obj,
            user=request.user,
            role=OrganizationMember.Role.OWNER,
        ).exists()


class IsOrganizationOwnerOrAdmin(BasePermission):
    """Разрешает доступ владельцу или админу организации."""

    def has_object_permission(self, request, view, obj):
        return OrganizationMember.objects.filter(
            organization=obj,
            user=request.user,
            role__in=[
                OrganizationMember.Role.OWNER,
                OrganizationMember.Role.ADMIN,
            ],
        ).exists()
