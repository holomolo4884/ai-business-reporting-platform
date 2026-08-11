from django.urls import path

from organizations.views import (
    OrganizationDetailView,
    OrganizationListCreateView,
)

urlpatterns = [
    path(
        "organizations/",
        OrganizationListCreateView.as_view(),
        name="organization-list-create",
    ),
    path(
        "organizations/<int:organization_id>/",
        OrganizationDetailView.as_view(),
        name="organization-detail",
    ),
]
