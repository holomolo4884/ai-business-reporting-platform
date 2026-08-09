from rest_framework import serializers

from accounts.models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(min_length=8, write_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "password",
            "first_name",
            "last_name",
        )
        extra_kwargs = {
            "username": {"required": False, "allow_blank": True},
            "first_name": {"required": False, "allow_blank": True},
            "last_name": {"required": False, "allow_blank": True},
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует!")
        return value

    def create(self, validated_data):
        # Если username не указан, генерируем из email
        if not validated_data.get("username"):
            email = validated_data["email"]
            username = email.split("@")[0]
            # Добавляем суффикс, если username уже занят
            base_username = username
            counter = 1
            while User.objects.filter(username=base_username).exists():
                username = f"{base_username}_{counter}"
                counter += 1
            validated_data["username"] = username

        user = User.objects.create_user(**validated_data)
        return user
