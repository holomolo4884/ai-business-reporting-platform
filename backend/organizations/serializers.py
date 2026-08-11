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


class OrganizationMemberSerializer(serializers.ModelSerializer):
    """Serializer для получения данных участника организации."""

    user_email = serializers.CharField(source="user.email", read_only=True)
    user_username = serializers.CharField(source="user.username", read_only=True)
    user_first_name = serializers.CharField(source="user.first_name", read_only=True)
    user_last_name = serializers.CharField(source="user.last_name", read_only=True)

    class Meta:
        model = OrganizationMember
        fields = (
            "id",
            "user",
            "user_email",
            "user_username",
            "user_first_name",
            "user_last_name",
            "role",
            "created_at",
        )
        read_only_fields = ("id", "user", "created_at")


class OrganizationMemberAddSerializer(serializers.Serializer):
    """Serializer для добавления участника в организацию."""

    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=OrganizationMember.Role.choices,
        default=OrganizationMember.Role.MEMBER,
    )

    def validate_email(self, value):
        from accounts.models import User

        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким адресом электронной почты не существует."
            )
        return value

    def validate(self, data):
        request = self.context.get("request")
        organization = self.context.get("organization")

        if request and organization:
            from accounts.models import User

            user = User.objects.get(email=data["email"])

            # Проверяем, не является ли пользователь уже участником
            if OrganizationMember.objects.filter(
                organization=organization,
                user=user,
            ).exists():
                raise serializers.ValidationError(
                    "Пользователь уже является членом этой организации."
                )

        return data


class OrganizationMemberUpdateSerializer(serializers.ModelSerializer):
    """Serializer для обновления роли участника."""

    class Meta:
        model = OrganizationMember
        fields = ("role",)
