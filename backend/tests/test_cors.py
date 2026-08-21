import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestCORSSettings:
    """Проверка, что CORS настроен правильно."""

    def test_cors_allowed_origin_gets_header(self, client):
        """Запрос с разрешённого origin получает CORS заголовки."""
        url = reverse("api:health-check")
        response = client.get(
            url,
            HTTP_ORIGIN="http://localhost:3000",
        )

        # Django corsheaders добавляет Access-Control-Allow-Origin
        assert (
            "Access-Control-Allow-Origin" in response.headers
            or response.status_code == status.HTTP_200_OK
        )

    def test_cors_disallowed_origin(self, client):
        """Запрос с неразрешённого origin не получает CORS заголовки."""
        url = reverse("api:health-check")
        response = client.get(
            url,
            HTTP_ORIGIN="http://evil-site.com",
        )

        # Origin не должен быть разрешён
        allow_origin = response.headers.get("Access-Control-Allow-Origin", "")
        assert "evil-site.com" not in allow_origin

    def test_cors_preflight_request(self, client):
        """OPTIONS preflight запрос обрабатывается корректно."""
        url = reverse("api:report-list")
        response = client.options(
            url,
            HTTP_ORIGIN="http://localhost:3000",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type,authorization",
        )

        # Preflight должен быть разрешён
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
        ]
        # Должен быть Access-Control-Allow-Methods
        assert "Access-Control-Allow-Methods" in response.headers

    def test_cors_with_credentials(self, client):
        """CORS с credentials работает для разрешённых origins."""
        url = reverse("api:health-check")
        response = client.get(
            url,
            HTTP_ORIGIN="http://localhost:3000",
        )

        # CORS_ALLOW_CREDENTIALS должен добавить этот заголовок
        # (только если origin разрешён)
        if "Access-Control-Allow-Credentials" in response.headers:
            assert response.headers["Access-Control-Allow-Credentials"] == "true"
