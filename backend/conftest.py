import pytest
from rest_framework.test import APIClient

from accounts.models import User


@pytest.fixture
def api_client():
    """Клиент для тестирования API."""
    return APIClient()


@pytest.fixture
def test_user(db):
    """Тестовый пользователь."""
    return User.objects.create_user(
        email="test@example.com",
        password="testpassword123",
        username="testuser",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def authenticated_client(api_client, test_user):
    """Аутентифицированный клиент с JWT токеном."""
    response = api_client.post(
        "/api/v1/auth/token/",
        {"email": test_user.email, "password": "testpassword123"},
        format="json",
    )
    access_token = response.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    return api_client
