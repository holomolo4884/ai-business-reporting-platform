from django.urls import path

from reports.views import ReportGenerateView, ReportListView

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
]
