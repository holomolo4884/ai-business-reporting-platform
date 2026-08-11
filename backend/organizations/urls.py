from django.urls import path

from organizations.views import (
    OrganizationDetailView,
    OrganizationListCreateView,
    OrganizationMemberDetailView,
    OrganizationMemberListView,
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
    path(
        "organizations/<int:organization_id>/members/",
        OrganizationMemberListView.as_view(),
        name="organization-member-list",
    ),
    path(
        "organizations/<int:organization_id>/members/<int:member_id>/",
        OrganizationMemberDetailView.as_view(),
        name="organization-member-detail",
    ),
]
