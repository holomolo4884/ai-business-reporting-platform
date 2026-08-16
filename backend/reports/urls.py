from django.urls import path

from reports.views import ReportDetailView, ReportGenerateView, ReportListView

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
]
