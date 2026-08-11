from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from organizations.models import Organization, OrganizationMember
from organizations.permissions import (
    IsOrganizationMember,
    IsOrganizationOwner,
    IsOrganizationOwnerOrAdmin,
)
from organizations.serializers import (
    OrganizationCreateSerializer,
    OrganizationMemberAddSerializer,
    OrganizationMemberSerializer,
    OrganizationMemberUpdateSerializer,
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
                {"detail": "Редактировать организацию может только владелец или администратор."},
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
                {"detail": "Только владелец может удалить организацию."},
                status=status.HTTP_403_FORBIDDEN,
            )

        organization.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrganizationMemberListView(APIView):
    """Список участников организации и добавление нового."""

    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def get_organization(self, organization_id: int) -> Organization:
        return Organization.objects.get(id=organization_id)

    def get(self, request: Request, organization_id: int) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)

        members = organization.members.select_related("user").all()
        serializer = OrganizationMemberSerializer(members, many=True)
        return Response(serializer.data)

    def post(self, request: Request, organization_id: int) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)

        # Проверка: только owner или admin могут добавлять участников
        if not IsOrganizationOwnerOrAdmin().has_object_permission(request, self, organization):
            return Response(
                {"detail": "Только владелец или администратор может добавлять участников."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = OrganizationMemberAddSerializer(
            data=request.data,
            context={"request": request, "organization": organization},
        )
        serializer.is_valid(raise_exception=True)

        from accounts.models import User

        user = User.objects.get(email=serializer.validated_data["email"])
        role = serializer.validated_data["role"]

        member = OrganizationMember.objects.create(
            organization=organization,
            user=user,
            role=role,
        )

        return Response(
            OrganizationMemberSerializer(member).data,
            status=status.HTTP_201_CREATED,
        )


class OrganizationMemberDetailView(APIView):
    """Обновление роли и удаление участника."""

    permission_classes = [IsAuthenticated, IsOrganizationMember]

    def get_organization(self, organization_id: int) -> Organization:
        return Organization.objects.get(id=organization_id)

    def get_member(self, organization_id: int, member_id: int) -> OrganizationMember:
        return OrganizationMember.objects.get(
            id=member_id,
            organization_id=organization_id,
        )

    def patch(self, request: Request, organization_id: int, member_id: int) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)

        # Проверка: только owner может менять роли
        if not IsOrganizationOwner().has_object_permission(request, self, organization):
            return Response(
                {"detail": "Только владелец может изменять роли участников."},
                status=status.HTTP_403_FORBIDDEN,
            )

        member = self.get_member(organization_id, member_id)

        # Нельзя менять роль последнего owner'а
        if member.is_owner:
            owners_count = organization.members.filter(role=OrganizationMember.Role.OWNER).count()
            if owners_count == 1:
                new_role = request.data.get("role")
                if new_role != OrganizationMember.Role.OWNER:
                    return Response(
                        {"detail": "Невозможно изменить роль последнего владельца."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        serializer = OrganizationMemberUpdateSerializer(
            member,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        member = serializer.save()

        return Response(OrganizationMemberSerializer(member).data)

    def delete(self, request: Request, organization_id: int, member_id: int) -> Response:
        organization = self.get_organization(organization_id)
        self.check_object_permissions(request, organization)

        # Проверка: только owner или admin могут удалять участников
        if not IsOrganizationOwnerOrAdmin().has_object_permission(request, self, organization):
            return Response(
                {"detail": "Только владелец или администратор может удалять участников."},
                status=status.HTTP_403_FORBIDDEN,
            )

        member = self.get_member(organization_id, member_id)

        # Нельзя удалить последнего owner'а
        if member.is_owner:
            owners_count = organization.members.filter(role=OrganizationMember.Role.OWNER).count()
            if owners_count == 1:
                return Response(
                    {"detail": "Не удается удалить последнего владельца."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
