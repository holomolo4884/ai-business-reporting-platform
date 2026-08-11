from rest_framework import serializers

from organizations.models import Organization, OrganizationMember


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer для получения данных организации."""

    members_count = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = (
            "id",
            "name",
            "description",
            "created_at",
            "updated_at",
            "members_count",
            "user_role",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def get_members_count(self, obj) -> int:
        return obj.members.count()

    def get_user_role(self, obj) -> str | None:
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            membership = obj.members.filter(user=request.user).first()
            if membership:
                return membership.role
        return None


class OrganizationCreateSerializer(serializers.ModelSerializer):
    """Serializer для создания организации."""

    class Meta:
        model = Organization
        fields = ("name", "description")

    def create(self, validated_data):
        # Создаём организацию
        organization = Organization.objects.create(**validated_data)

        # Автоматически добавляем создателя как владельца
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            OrganizationMember.objects.create(
                organization=organization,
                user=request.user,
                role=OrganizationMember.Role.OWNER,
            )

        return organization


class OrganizationUpdateSerializer(serializers.ModelSerializer):
    """Serializer для обновления организации."""

    class Meta:
        model = Organization
        fields = ("name", "description")
