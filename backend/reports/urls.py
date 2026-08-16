from django.urls import path

from reports.views import (
    ReportDetailView,
    ReportDownloadView,
    ReportGenerateView,
    ReportListView,
    ReportRegenerateView,
)

urlpatterns = [
    path(
        "reports/generate/",
        ReportGenerateView.as_view(),
        name="report-generate",
    ),
    path(
        "reports/",
        ReportListView.as_view(),
        name="report-list",
    ),
    path(
        "reports/<int:report_id>/",
        ReportDetailView.as_view(),
        name="report-detail",
    ),
    path(
        "reports/<int:report_id>/regenerate/",
        ReportRegenerateView.as_view(),
        name="report-regenerate",
    ),
    path(
        "reports/<int:report_id>/download/",
        ReportDownloadView.as_view(),
        name="report-download",
    ),
]
