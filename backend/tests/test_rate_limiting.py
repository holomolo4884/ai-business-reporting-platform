import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status


@pytest.fixture(autouse=True)
def clear_cache():
    """Очищает cache перед каждым тестом."""
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestLoginRateLimit:
    """Проверка rate limit на login endpoint."""

    def test_login_rate_limit_blocks_after_5_attempts(self, client):
        """После 5 попыток логина — 429 Too Many Requests."""
        url = reverse("api:token_obtain_pair")

        # Делаем 6 попыток с неверным паролем
        responses = []
        for _ in range(6):
            response = client.post(
                url,
                {"email": "wrong@example.com", "password": "wrong"},
                content_type="application/json",
            )
            responses.append(response.status_code)

        # Первые 5 должны быть 401 (Unauthorized)
        assert responses[:5].count(status.HTTP_401_UNAUTHORIZED) == 5
        # 6-я должна быть 429 (Too Many Requests)
        assert responses[5] == status.HTTP_429_TOO_MANY_REQUESTS

    def test_login_rate_limit_resets_after_time(self, client):
        """Rate limit сбрасывается по прошествии времени."""
        url = reverse("api:token_obtain_pair")

        # Делаем 5 попыток
        for _ in range(5):
            client.post(
                url,
                {"email": "wrong@example.com", "password": "wrong"},
                content_type="application/json",
            )

        # Очищаем кеш (имитация прошествия времени)
        cache.clear()

        # 6-я попытка должна пройти (не 429)
        response = client.post(
            url,
            {"email": "wrong@example.com", "password": "wrong"},
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestReportGenerateRateLimit:
    """Проверка rate limit на генерацию отчётов."""

    def test_report_generate_rate_limit(self, authenticated_client, test_organization):
        """После 10 генераций — 429 Too Many Requests."""
        url = reverse("api:report-generate")
        data = {
            "organization_id": test_organization.id,
            "report_type": "sales",
            "period_start": "2026-01-01T00:00:00Z",
            "period_end": "2026-01-31T23:59:59Z",
        }

        # Делаем 11 запросов
        responses = []
        for _ in range(11):
            response = authenticated_client.post(
                url,
                data,
                content_type="application/json",
            )
            responses.append(response.status_code)

        # Первые 10 должны быть 202 (Accepted)
        assert responses[:10].count(status.HTTP_202_ACCEPTED) == 10
        # 11-я должна быть 429 (Too Many Requests)
        assert responses[10] == status.HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.django_db
class TestGeneralRateLimit:
    """Проверка общего rate limit."""

    def test_anon_rate_limit(self, client):
        """Анонимный пользователь ограничен 60 запросами в минуту."""
        url = reverse("api:health-check")

        # Делаем 65 запросов
        responses = []
        for _ in range(65):
            response = client.get(url)
            responses.append(response.status_code)

        # Большинство должны быть 200
        assert responses.count(status.HTTP_200_OK) >= 55
        # Последние должны быть 429
        assert status.HTTP_429_TOO_MANY_REQUESTS in responses

    def test_user_rate_limit(self, authenticated_client):
        """Авторизованный пользователь ограничен 300 запросами в минуту."""
        url = reverse("api:report-list")

        # Делаем 305 запросов
        responses = []
        for _ in range(305):
            response = authenticated_client.get(url)
            responses.append(response.status_code)

        # Большинство должны быть 200
        assert responses.count(status.HTTP_200_OK) >= 295
        # Последние должны быть 429
        assert status.HTTP_429_TOO_MANY_REQUESTS in responses
