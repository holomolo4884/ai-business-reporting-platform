import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestTokenObtain:
    """Тесты получения JWT токенов."""

    def test_obtain_token_success(self, api_client, test_user):
        """Успешное получение токенов."""
        url = reverse("api:token_obtain_pair")
        data = {
            "email": test_user.email,
            "password": "testpassword123",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_obtain_token_with_wrong_password(self, api_client, test_user):
        """Получение токенов с неверным паролем должно вернуть ошибку."""
        url = reverse("api:token_obtain_pair")
        data = {
            "email": test_user.email,
            "password": "wrongpassword",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == 401
        assert "detail" in response.data

    def test_obtain_token_with_nonexistent_user(self, api_client):
        """Получение токенов для несуществующего пользователя."""
        url = reverse("api:token_obtain_pair")
        data = {
            "email": "nonexistent@example.com",
            "password": "somepassword",
        }

        response = api_client.post(url, data, format="json")

        assert response.status_code == 401


@pytest.mark.django_db
class TestTokenRefresh:
    """Тесты обновления JWT токенов."""

    def test_refresh_token_success(self, api_client, test_user):
        """Успешное обновление access токена."""
        # Получаем токены
        obtain_url = reverse("api:token_obtain_pair")
        response = api_client.post(
            obtain_url,
            {"email": test_user.email, "password": "testpassword123"},
            format="json",
        )
        refresh_token = response.data["refresh"]

        # Обновляем токен
        refresh_url = reverse("api:token_refresh")
        response = api_client.post(
            refresh_url,
            {"refresh": refresh_token},
            format="json",
        )

        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_refresh_token_with_invalid_token(self, api_client):
        """Обновление с невалидным токеном должно вернуть ошибку."""
        url = reverse("api:token_refresh")
        response = api_client.post(
            url,
            {"refresh": "invalid_token"},
            format="json",
        )

        assert response.status_code == 401
