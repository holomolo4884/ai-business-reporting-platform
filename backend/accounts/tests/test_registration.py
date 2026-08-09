import pytest
from django.urls import reverse

from accounts.models import User


@pytest.mark.django_db
class TestRegistration:
    """Тесты регистрации пользователей."""

    def test_register_success(self, api_client):
        """Успешная регистрация нового пользователя."""
        url = reverse("api:register")
        data = {
            "email": "newuser@example.com",
            "password": "securepassword123",
            "first_name": "John",
            "last_name": "Doe",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == 201
        assert response.data["email"] == "newuser@example.com"
        assert response.data["username"] == "newuser"
        assert response.data["first_name"] == "John"
        assert response.data["last_name"] == "Doe"
        assert "password" not in response.data

        # Проверяем, что пользователь создан в базе
        assert User.objects.filter(email="newuser@example.com").exists()

    def test_register_generates_username_from_email(self, api_client):
        """Username генерируется из email, если не указан."""
        url = reverse("api:register")
        data = {
            "email": "john.doe@example.com",
            "password": "securepassword123",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == 201
        assert response.data["username"] == "john.doe"

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

    def test_register_with_short_password(self, api_client):
        """Регистрация с коротким паролем должна вернуть ошибку."""
        url = reverse("api:register")
        data = {
            "email": "newuser@example.com",
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
