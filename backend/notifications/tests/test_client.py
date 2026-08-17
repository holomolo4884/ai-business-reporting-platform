from unittest.mock import MagicMock, patch

import httpx
import pytest

from notifications.client import (
    NotificationAuthenticationError,
    NotificationChannel,
    NotificationClient,
    NotificationServiceUnavailableError,
)


class TestNotificationClient:
    """Тесты NotificationClient."""

    def test_client_initialization(self):
        """Клиент корректно инициализируется."""
        client = NotificationClient(
            base_url="http://localhost:8001",
            api_key="test-key",
            timeout=10,
        )
        assert client.base_url == "http://localhost:8001"
        assert client.api_key == "test-key"
        assert client.timeout == 10

    def test_client_removes_trailing_slash(self):
        """Клиент удаляет trailing slash из URL."""
        client = NotificationClient(base_url="http://localhost:8001/")
        assert client.base_url == "http://localhost:8001"

    @patch("notifications.client.client.httpx.Client")
    def test_send_notification_success(self, mock_client_class):
        """Успешная отправка уведомления."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "message": "Отправлено",
            "notification_id": "abc-123",
            "error_details": None,
        }
        mock_client.post.return_value = mock_response
        mock_client.__enter__.return_value = mock_client
        mock_client_class.return_value = mock_client

        client = NotificationClient(
            base_url="http://localhost:8001",
            api_key="test-key",
        )
        response = client.send_notification(
            channel=NotificationChannel.EMAIL,
            recipient="test@example.com",
            subject="Test",
            message="Hello",
        )

        assert response.success is True
        assert response.notification_id == "abc-123"

        # Проверяем, что API ключ был отправлен
        call_args = mock_client.post.call_args
        assert call_args.kwargs["headers"]["X-API-Key"] == "test-key"

    @patch("notifications.client.client.httpx.Client")
    def test_send_notification_connection_error(self, mock_client_class):
        """Ошибка подключения к notification-service."""
        mock_client = MagicMock()
        mock_client.post.side_effect = httpx.ConnectError("Connection refused")
        mock_client.__enter__.return_value = mock_client
        mock_client_class.return_value = mock_client

        client = NotificationClient()
        with pytest.raises(NotificationServiceUnavailableError):
            client.send_notification(
                channel=NotificationChannel.EMAIL,
                recipient="test@example.com",
                message="Hello",
            )

    @patch("notifications.client.client.httpx.Client")
    def test_send_notification_401_error(self, mock_client_class):
        """Ошибка 401 - неверный API ключ."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_client.post.return_value = mock_response
        mock_client.__enter__.return_value = mock_client
        mock_client_class.return_value = mock_client

        client = NotificationClient()
        with pytest.raises(NotificationAuthenticationError):
            client.send_notification(
                channel=NotificationChannel.EMAIL,
                recipient="test@example.com",
                message="Hello",
            )

    @patch("notifications.client.client.httpx.Client")
    def test_send_notification_500_error(self, mock_client_class):
        """Ошибка 500 - server error."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_client.post.return_value = mock_response
        mock_client.__enter__.return_value = mock_client
        mock_client_class.return_value = mock_client

        client = NotificationClient()
        with pytest.raises(NotificationServiceUnavailableError):
            client.send_notification(
                channel=NotificationChannel.EMAIL,
                recipient="test@example.com",
                message="Hello",
            )

    @patch("notifications.client.client.httpx.Client")
    def test_is_healthy_returns_true(self, mock_client_class):
        """Health check возвращает True."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response
        mock_client.__enter__.return_value = mock_client
        mock_client_class.return_value = mock_client

        client = NotificationClient()
        assert client.is_healthy() is True

    @patch("notifications.client.client.httpx.Client")
    def test_is_healthy_returns_false_on_error(self, mock_client_class):
        """Health check возвращает False при ошибке."""
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.ConnectError("Connection refused")
        mock_client.__enter__.return_value = mock_client
        mock_client_class.return_value = mock_client

        client = NotificationClient()
        assert client.is_healthy() is False
