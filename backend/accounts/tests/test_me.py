import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestMeEndpoint:
    """Тесты получения текущего пользователя."""

    def test_me_success(self, authenticated_client, test_user):
        """Успешное получение данных текущего пользователя."""
        url = reverse("api:me")

        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert response.data["email"] == test_user.email
        assert response.data["username"] == test_user.username
        assert response.data["first_name"] == test_user.first_name
        assert response.data["last_name"] == test_user.last_name
        assert "password" not in response.data

    def test_me_without_auth(self, api_client):
        """Запрос без токена должен вернуть 401."""
        url = reverse("api:me")

        response = api_client.get(url)

        assert response.status_code == 401

    def test_me_with_invalid_token(self, api_client):
        """Запрос с невалидным токеном должен вернуть 401."""
        url = reverse("api:me")
        api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token")

        response = api_client.get(url)

        assert response.status_code == 401
