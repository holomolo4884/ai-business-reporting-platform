from django.urls import path

from reports.views import ReportGenerateView

urlpatterns = [
    path(
        "reports/generate/",
        ReportGenerateView.as_view(),
        name="report-generate",
    ),
]
