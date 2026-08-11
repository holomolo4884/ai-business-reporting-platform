from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from organizations.models import Organization
from organizations.permissions import (
    IsOrganizationMember,
    IsOrganizationOwner,
    IsOrganizationOwnerOrAdmin,
)
from organizations.serializers import (
    OrganizationCreateSerializer,
    OrganizationSerializer,
    OrganizationUpdateSerializer,
)


class OrganizationListCreateView(APIView):
    """Список организаций пользователя и создание новой."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        # Получаем только организации, в которых пользователь является участником
        organizations = Organization.objects.filter(members__user=request.user).distinct()

        serializer = OrganizationSerializer(
            organizations,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)

    def post(self, request: Request) -> Response:
        serializer = OrganizationCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        organization = serializer.save()

        return Response(
            OrganizationSerializer(
                organization,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class OrganizationDetailView(APIView):
    """Детали, обновление и удаление организации."""

    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def get_object(self, organization_id: int) -> Organization:
        return Organization.objects.get(id=organization_id)

    def get(self, request: Request, organization_id: int) -> Response:
        organization = self.get_object(organization_id)
        self.check_object_permissions(request, organization)

        serializer = OrganizationSerializer(
            organization,
            context={"request": request},
        )
        return Response(serializer.data)

    def patch(self, request: Request, organization_id: int) -> Response:
        organization = self.get_object(organization_id)
        self.check_object_permissions(request, organization)

        # Проверка: только owner или admin могут редактировать
        if not IsOrganizationOwnerOrAdmin().has_object_permission(request, self, organization):
            return Response(
                {"detail": "Only owner or admin can edit organization."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = OrganizationUpdateSerializer(
            organization,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        organization = serializer.save()

        return Response(
            OrganizationSerializer(
                organization,
                context={"request": request},
            ).data
        )

    def delete(self, request: Request, organization_id: int) -> Response:
        organization = self.get_object(organization_id)
        self.check_object_permissions(request, organization)

        # Проверка: только owner может удалить
        if not IsOrganizationOwner().has_object_permission(request, self, organization):
            return Response(
                {"detail": "Only owner can delete organization."},
                status=status.HTTP_403_FORBIDDEN,
            )

        organization.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
