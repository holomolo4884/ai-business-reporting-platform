import pytest
from django.urls import reverse

from accounts.models import User


@pytest.mark.django_db
class TestRegistration:
    """Тесты регистрации пользователей."""

    def test_register_success(self, api_client, faker):
        """Успешная регистрация нового пользователя."""
        url = reverse("api:register")
        # Используем faker для генерации уникального email
        unique_email = faker.email()
        data = {
            "email": unique_email,
            "password": "securepassword123",
            "first_name": "John",
            "last_name": "Doe",
        }

        response = api_client.post(url, data, format="json")

        # Отладочный вывод
        print("\n\n=== ОТЛАДКА ===")
        print(f"Email: {unique_email}")
        print(f"Status code: {response.status_code}")
        print(f"Response data: {response.data}")
        print("=== КОНЕЦ ОТЛАДКИ ===\n")

        assert response.status_code == 201
        assert response.data["email"] == unique_email
        assert "username" in response.data  # username генерируется автоматически
        assert response.data["first_name"] == "John"
        assert response.data["last_name"] == "Doe"
        assert "password" not in response.data

        # Проверяем, что пользователь создан в базе
        assert User.objects.filter(email=unique_email).exists()

    def test_register_generates_username_from_email(self, api_client, faker):
        """Username генерируется из email, если не указан."""
        url = reverse("api:register")
        unique_email = faker.email()
        data = {
            "email": unique_email,
            "password": "securepassword123",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == 201
        # Username должен быть сгенерирован из email
        assert "username" in response.data

    def test_register_with_existing_email(self, api_client, test_user):
        """Регистрация с уже существующим email должна вернуть ошибку."""
        url = reverse("api:register")
        data = {
            "email": test_user.email,
            "password": "securepassword123",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == 400
        assert "email" in response.data

    def test_register_with_short_password(self, api_client, faker):
        """Регистрация с коротким паролем должна вернуть ошибку."""
        url = reverse("api:register")
        unique_email = faker.email()
        data = {
            "email": unique_email,
            "password": "short",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == 400
        assert "password" in response.data

    def test_register_with_invalid_email(self, api_client):
        """Регистрация с невалидным email должна вернуть ошибку."""
        url = reverse("api:register")
        data = {
            "email": "not-an-email",
            "password": "securepassword123",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == 400
        assert "email" in response.data
