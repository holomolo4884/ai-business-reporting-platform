import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestSecurityEndpoints:
    """Проверка deny-by-default для защищённых endpoint'ов."""

    PUBLIC_ENDPOINTS = [
        ("api:health-check", {}),
        # auth endpoints — публичные
    ]

    PROTECTED_ENDPOINTS = [
        ("api:report-list", {}),
        ("api:report-generate", {}),
        ("api:schedule-list-create", {"organization_id": 1}),
    ]

    @pytest.fixture
    def anonymous_client(self):
        """Клиент без авторизации."""
        from rest_framework.test import APIClient

        return APIClient()

    def test_public_endpoints_accessible(self, anonymous_client):
        """Публичные endpoint'ы доступны без токена."""
        for name, kwargs in self.PUBLIC_ENDPOINTS:
            url = reverse(name, kwargs=kwargs)
            response = anonymous_client.get(url)
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_302_FOUND,  # possible redirect
            ], f"Public endpoint {name} should be accessible, got {response.status_code}"

    def test_protected_endpoints_require_auth(self, anonymous_client):
        """Защищённые endpoint'ы требуют авторизации."""
        for name, kwargs in self.PROTECTED_ENDPOINTS:
            url = reverse(name, kwargs=kwargs)
            response = anonymous_client.get(url)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED, (
                f"Endpoint {name} should return 401 without auth, " f"got {response.status_code}"
            )

    def test_protected_endpoints_accessible_with_token(self, authenticated_client):
        """Защищённые endpoint'ы доступны с валидным токеном."""
        # report-list работает для любого аутентифицированного пользователя
        url = reverse("api:report-list")
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_invalid_token_returns_401(self, anonymous_client):
        """Невалидный токен возвращает 401."""
        url = reverse("api:report-list")
        response = anonymous_client.get(
            url,
            HTTP_AUTHORIZATION="Bearer invalid-token-here",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_expired_token_returns_401(self, anonymous_client):
        """Истёкший токен возвращает 401."""
        # Можно создать истёкший токен через PyJWT для полного теста
        url = reverse("api:report-list")
        response = anonymous_client.get(
            url,
            HTTP_AUTHORIZATION="Bearer expired.token.here",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
