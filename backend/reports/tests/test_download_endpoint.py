import pytest
from django.core.files.base import ContentFile
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from organizations.models import Organization, OrganizationMember
from reports.models import Report


@pytest.mark.django_db
class TestReportDownloadEndpoint:
    """Тесты GET /api/v1/reports/{id}/download/"""

    def test_download_completed_report(self, authenticated_client, test_user, test_organization):
        """Успешное скачивание завершённого отчёта."""
        now = timezone.now()

        report = Report.objects.create(
            organization=test_organization,
            created_by=test_user,
            report_type=Report.ReportType.SALES,
            period_start=now - timezone.timedelta(days=30),
            period_end=now,
            status=Report.Status.COMPLETED,
            metrics={"revenue": 100000},
            generated_text="Test report",
        )

        pdf_content = b"%PDF-1.4\nTest PDF content"
        report.pdf_file.save(
            f"report_{report.id}.pdf",
            ContentFile(pdf_content),
            save=True,
        )

        url = reverse("api:report-download", kwargs={"report_id": report.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/pdf"
        assert "attachment" in response["Content-Disposition"]
        assert f"report_{report.id}.pdf" in response["Content-Disposition"]
        content = b"".join(response.streaming_content)
        assert len(content) > 0
        assert content.startswith(b"%PDF")

    def test_download_pending_report_fails(
        self, authenticated_client, test_user, test_organization
    ):
        """Скачивание незавершённого отчёта возвращает 400."""
        now = timezone.now()

        report = Report.objects.create(
            organization=test_organization,
            created_by=test_user,
            report_type=Report.ReportType.SALES,
            period_start=now - timezone.timedelta(days=30),
            period_end=now,
            status=Report.Status.PENDING,
        )

        url = reverse("api:report-download", kwargs={"report_id": report.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.json()

    def test_download_without_auth_fails(self, api_client, test_user, test_organization):
        """Скачивание без авторизации возвращает 401."""
        now = timezone.now()

        report = Report.objects.create(
            organization=test_organization,
            created_by=test_user,
            report_type=Report.ReportType.SALES,
            period_start=now - timezone.timedelta(days=30),
            period_end=now,
            status=Report.Status.COMPLETED,
        )

        url = reverse("api:report-download", kwargs={"report_id": report.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_download_nonexistent_report_fails(self, authenticated_client):
        """Скачивание несуществующего отчёта возвращает 404."""
        url = reverse("api:report-download", kwargs={"report_id": 99999})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_download_other_user_report_fails(self, outsider_client):
        """Скачивание чужого отчёта возвращает 403/404."""
        from accounts.models import User

        other_user, _ = User.objects.get_or_create(
            email="other_download@example.com",
            defaults={"username": "other_download"},
        )
        other_user.set_password("otherpass123")
        other_user.save()

        other_org, _ = Organization.objects.get_or_create(
            name="Other Download Org",
        )
        OrganizationMember.objects.get_or_create(
            organization=other_org,
            user=other_user,
            defaults={"role": OrganizationMember.Role.OWNER},
        )

        now = timezone.now()
        other_report = Report.objects.create(
            organization=other_org,
            created_by=other_user,
            report_type=Report.ReportType.SALES,
            period_start=now - timezone.timedelta(days=30),
            period_end=now,
            status=Report.Status.COMPLETED,
        )

        pdf_content = b"%PDF-1.4\nTest PDF content"
        other_report.pdf_file.save(
            f"report_{other_report.id}.pdf",
            ContentFile(pdf_content),
            save=True,
        )

        url = reverse("api:report-download", kwargs={"report_id": other_report.id})
        response = outsider_client.get(url)

        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ]
