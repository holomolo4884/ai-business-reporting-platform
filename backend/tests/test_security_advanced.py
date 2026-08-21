from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.urls import reverse
from rest_framework import status

from reports.models import Report


@pytest.mark.django_db
class TestSQLInjection:
    """Проверка защиты от SQL-инъекций."""

    def test_sql_injection_in_search_parameter(self, authenticated_client):
        """SQL-инъекция в параметрах поиска не работает."""
        url = reverse("api:report-list")

        malicious = "'; DROP TABLE reports_report; --"
        response = authenticated_client.get(url, {"search": malicious})

        # Должен быть 200 (пустой список) или 400, но НЕ 500
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
        ]

    def test_sql_injection_in_ordering(self, authenticated_client):
        """SQL-инъекция через параметр сортировки не работает."""
        url = reverse("api:report-list")

        malicious = "id; DROP TABLE reports_report"
        response = authenticated_client.get(url, {"ordering": malicious})

        # Django filter валидирует ordering параметры
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
        ]

    def test_sql_injection_in_filter(self, authenticated_client):
        """SQL-инъекция в filter параметрах не работает."""
        url = reverse("api:report-list")

        malicious = "1 OR 1=1; DROP TABLE reports_report"
        response = authenticated_client.get(url, {"status": malicious})

        # Фильтр не найдёт совпадений, но не упадёт
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
        ]


@pytest.mark.django_db
class TestFileValidation:
    """Проверка валидации загружаемых файлов."""

    def test_pdf_file_accepts_pdf_extension(self, test_user, test_organization):
        """PDF файл с расширением .pdf принимается."""
        from django.utils import timezone  # noqa: E402

        now = timezone.now()
        report = Report(
            organization=test_organization,
            created_by=test_user,
            report_type=Report.ReportType.SALES,
            status=Report.Status.COMPLETED,
            period_start=now - timedelta(days=30),
            period_end=now,
        )

        # Создаём валидный PDF (минимальный валидный PDF)
        pdf_content = b"%PDF-1.4\n% fake pdf content"
        report.pdf_file.save(
            "test_report.pdf",
            ContentFile(pdf_content),
            save=False,
        )

        # Валидация не должна вызывать ошибок
        report.full_clean()

    def test_pdf_file_rejects_exe_extension(self, test_user, test_organization):
        """Файл с расширением .exe отклоняется."""
        from django.utils import timezone  # noqa: E402

        now = timezone.now()
        report = Report(
            organization=test_organization,
            created_by=test_user,
            report_type=Report.ReportType.SALES,
            status=Report.Status.COMPLETED,
            period_start=now - timedelta(days=30),
            period_end=now,
        )

        # Пытаемся загрузить .exe файл
        exe_content = b"MZ... fake exe content"
        report.pdf_file.save(
            "malware.exe",
            ContentFile(exe_content),
            save=False,
        )

        # Валидация должна вызвать ошибку
        with pytest.raises(ValidationError) as exc_info:
            report.full_clean()

        assert "pdf_file" in exc_info.value.message_dict

    def test_pdf_file_rejects_js_extension(self, test_user, test_organization):
        """Файл с расширением .js отклоняется."""
        from django.utils import timezone  # noqa: E402

        now = timezone.now()
        report = Report(
            organization=test_organization,
            created_by=test_user,
            report_type=Report.ReportType.SALES,
            status=Report.Status.COMPLETED,
            period_start=now - timedelta(days=30),
            period_end=now,
        )

        js_content = b"alert('xss');"
        report.pdf_file.save(
            "script.js",
            ContentFile(js_content),
            save=False,
        )

        with pytest.raises(ValidationError) as exc_info:
            report.full_clean()

        assert "pdf_file" in exc_info.value.message_dict


@pytest.mark.django_db
class TestXSS:
    """Проверка защиты от XSS."""

    def test_report_generated_text_escapes_html(self, test_user, test_organization):
        """HTML в generated_text экранируется при рендеринге."""
        from django.utils import timezone  # noqa: E402

        from reports.renderers import ReportRenderer  # noqa: E402

        now = timezone.now()
        # AI response содержит опасный HTML в summary
        report = Report(
            organization=test_organization,
            created_by=test_user,
            report_type=Report.ReportType.SALES,
            status=Report.Status.COMPLETED,
            ai_response={
                "summary": "<script>alert('xss')</script>Анализ показывает рост.",
                "insights": [],
                "recommendations": [],
            },
            generated_text="<script>alert('xss')</script>Нормальный текст",
            metrics={"revenue": 1000},
            period_start=now - timedelta(days=30),
            period_end=now,
        )
        report.save()

        renderer = ReportRenderer(report)
        html = renderer.render_html()

        # Проверяем, что в HTML нет реального <script> тега
        assert "<script>alert" not in html
        # Но экранированная версия может присутствовать
        assert "&lt;script&gt;" in html or "<script>" not in html

    def test_organization_name_escapes_html(self, test_user):
        """HTML в названии организации экранируется."""
        from django.utils import timezone  # noqa: E402

        from organizations.models import Organization  # noqa: E402
        from reports.renderers import ReportRenderer  # noqa: E402

        org = Organization.objects.create(name="<img src=x onerror=alert('xss')> Evil Corp")

        now = timezone.now()
        report = Report(
            organization=org,
            created_by=test_user,
            report_type=Report.ReportType.SALES,
            status=Report.Status.COMPLETED,
            generated_text="Отчёт",
            period_start=now - timedelta(days=30),
            period_end=now,
        )
        report.save()

        renderer = ReportRenderer(report)
        html = renderer.render_html()

        # Главное: <img должен быть экранирован как &lt;img
        assert (
            "<img src=x" not in html
        ), "XSS: реальный <img тег попал в HTML — должен быть экранирован"
        # Проверяем, что экранирование произошло
        assert "&lt;img" in html, "Ожидали экранирование &lt;img, но его нет"

    def test_metric_keys_cannot_inject_html(self, test_user, test_organization):
        """Ключи метрик не могут внедрить HTML."""
        from django.utils import timezone  # noqa: E402

        from reports.renderers import ReportRenderer  # noqa: E402

        now = timezone.now()
        report = Report(
            organization=test_organization,
            created_by=test_user,
            report_type=Report.ReportType.SALES,
            status=Report.Status.COMPLETED,
            generated_text="Отчёт",
            metrics={
                "<script>alert(1)</script>": 1000,
                "normal_metric": 500,
            },
            period_start=now - timedelta(days=30),
            period_end=now,
        )
        report.save()

        renderer = ReportRenderer(report)
        html = renderer.render_html()

        # Реальных <script> тегов быть не должно
        assert "<script>alert(1)</script>" not in html
