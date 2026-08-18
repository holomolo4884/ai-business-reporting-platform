import contextlib
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from celery.exceptions import Retry
from django.utils import timezone

from notifications.models import NotificationLog
from notifications.tasks import (
    send_report_notification_task,
    send_simple_notification,
)
from reports.models import Report


@pytest.fixture
def completed_report_for_notify(db, test_user):
    """Завершённый отчёт для тестов уведомлений."""
    from organizations.models import Organization, OrganizationMember  # noqa: E402

    org, _ = Organization.objects.get_or_create(name="Notify Test Org")
    OrganizationMember.objects.get_or_create(
        organization=org,
        user=test_user,
        defaults={"role": OrganizationMember.Role.OWNER},
    )

    now = timezone.now()
    report = Report.objects.create(
        organization=org,
        created_by=test_user,
        report_type=Report.ReportType.SALES,
        status=Report.Status.COMPLETED,
        period_start=now - timedelta(days=30),
        period_end=now,
        completed_at=now,
    )
    return report


@pytest.mark.django_db
class TestSendReportNotificationTask:
    """Тесты send_report_notification_task."""

    @patch("notifications.tasks.NotificationClient")
    def test_successful_notification(
        self, mock_client_class, completed_report_for_notify, test_user
    ):
        """Успешная отправка уведомления."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.notification_id = "notif-123"
        mock_response.error_details = None
        mock_client.send_notification.return_value = mock_response
        mock_client_class.return_value = mock_client

        send_report_notification_task(completed_report_for_notify.id, "email")

        log = NotificationLog.objects.filter(report=completed_report_for_notify).first()
        assert log is not None
        assert log.status == NotificationLog.Status.SUCCESS
        assert log.channel == NotificationLog.Channel.EMAIL
        assert log.recipient == test_user.email
        assert log.notification_id == "notif-123"
        assert log.sent_at is not None
        assert log.attempts == 1

    @patch("notifications.tasks.NotificationClient")
    def test_failed_notification_creates_log(self, mock_client_class, completed_report_for_notify):
        """При ошибке создаётся лог со статусом FAILED."""
        from notifications.client import NotificationError  # noqa: E402

        # Очищаем логи перед тестом
        NotificationLog.objects.all().delete()

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.success = False
        mock_response.message = "Ошибка отправки"
        mock_response.error_details = "SMTP error"
        mock_client.send_notification.return_value = mock_response
        mock_client_class.return_value = mock_client

        # В режиме EAGER + EAGER_PROPAGATES Celery может выбрасывать
        # как Retry, так и оригинальное исключение (NotificationError)
        with contextlib.suppress(Retry, NotificationError, Exception):
            send_report_notification_task(completed_report_for_notify.id, "email")

        log = NotificationLog.objects.filter(report=completed_report_for_notify).first()
        assert log is not None
        assert log.status == NotificationLog.Status.FAILED
        # error_details содержит str(NotificationError), который создан из response.message
        # или response.error_details (если был передан напрямую)
        assert log.error_details  # Не пустой
        assert len(log.error_details) > 0

    @patch("notifications.tasks.NotificationClient")
    def test_nonexistent_report_does_nothing(self, mock_client_class):
        """Для несуществующего отчёта задача ничего не делает."""
        # Запоминаем количество логов ДО теста
        initial_count = NotificationLog.objects.count()

        send_report_notification_task(99999, "email")

        # Проверяем, что НОВЫХ логов не появилось
        assert NotificationLog.objects.count() == initial_count
        mock_client_class.return_value.send_notification.assert_not_called()


@pytest.mark.django_db
class TestSendSimpleNotification:
    """Тесты send_simple_notification."""

    @patch("notifications.tasks.NotificationClient")
    def test_simple_notification_success(self, mock_client_class):
        """Простое уведомление отправляется успешно."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.success = True
        mock_response.notification_id = "simple-123"
        mock_response.error_details = None
        mock_client.send_notification.return_value = mock_response
        mock_client_class.return_value = mock_client

        send_simple_notification(
            channel="email",
            recipient="test@example.com",
            subject="Test",
            message="Hello",
        )

        log = NotificationLog.objects.filter(recipient="test@example.com").first()
        assert log is not None
        assert log.status == NotificationLog.Status.SUCCESS
        assert log.subject == "Test"

    @patch("notifications.tasks.NotificationClient")
    def test_simple_notification_failure(self, mock_client_class):
        """Ошибка в простом уведомлении логируется."""
        mock_client = MagicMock()
        mock_client.send_notification.side_effect = Exception("Network error")
        mock_client_class.return_value = mock_client

        send_simple_notification(
            channel="email",
            recipient="fail@example.com",
            message="Hello",
        )

        log = NotificationLog.objects.filter(recipient="fail@example.com").first()
        assert log is not None
        assert log.status == NotificationLog.Status.FAILED
        assert "Network error" in log.error_details
