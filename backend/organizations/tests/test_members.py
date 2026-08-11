import pytest
from django.urls import reverse

from organizations.models import OrganizationMember


@pytest.mark.django_db
class TestMemberList:
    """Тесты списка участников."""

    def test_list_members_as_owner(self, owner_client, test_organization):
        """Владелец видит список участников."""
        url = reverse(
            "api:organization-member-list", kwargs={"organization_id": test_organization.id}
        )

        response = owner_client.get(url)

        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_list_members_as_member(self, member_client, test_organization):
        """Участник видит список участников."""
        url = reverse(
            "api:organization-member-list", kwargs={"organization_id": test_organization.id}
        )

        response = member_client.get(url)

        assert response.status_code == 200

    def test_list_members_as_outsider(self, outsider_client, test_organization):
        """Пользователь вне организации не видит участников."""
        url = reverse(
            "api:organization-member-list", kwargs={"organization_id": test_organization.id}
        )

        response = outsider_client.get(url)

        assert response.status_code == 403


@pytest.mark.django_db
class TestMemberAdd:
    """Тесты добавления участников."""

    def test_add_member_as_owner(self, owner_client, test_organization, second_user):
        """Владелец может добавить участника."""
        url = reverse(
            "api:organization-member-list", kwargs={"organization_id": test_organization.id}
        )
        data = {
            "email": second_user.email,
            "role": "member",
        }

        response = owner_client.post(url, data, format="json")

        assert response.status_code == 201
        assert response.data["user_email"] == second_user.email
        assert response.data["role"] == "member"

    def test_add_member_as_admin(self, admin_client, test_organization, second_user):
        """Админ может добавить участника."""
        url = reverse(
            "api:organization-member-list", kwargs={"organization_id": test_organization.id}
        )
        data = {
            "email": second_user.email,
            "role": "member",
        }

        response = admin_client.post(url, data, format="json")

        assert response.status_code == 201

    def test_add_member_as_member(self, member_client, test_organization, second_user):
        """Обычный участник не может добавлять участников."""
        url = reverse(
            "api:organization-member-list", kwargs={"organization_id": test_organization.id}
        )
        data = {
            "email": second_user.email,
            "role": "member",
        }

        response = member_client.post(url, data, format="json")

        assert response.status_code == 403

    def test_add_existing_member(self, owner_client, test_organization, test_user):
        """Нельзя добавить пользователя, который уже участник."""
        url = reverse(
            "api:organization-member-list", kwargs={"organization_id": test_organization.id}
        )
        data = {
            "email": test_user.email,
            "role": "member",
        }

        response = owner_client.post(url, data, format="json")

        assert response.status_code == 400

    def test_add_nonexistent_user(self, owner_client, test_organization):
        """Нельзя добавить несуществующего пользователя."""
        url = reverse(
            "api:organization-member-list", kwargs={"organization_id": test_organization.id}
        )
        data = {
            "email": "nonexistent@example.com",
            "role": "member",
        }

        response = owner_client.post(url, data, format="json")

        assert response.status_code == 400


@pytest.mark.django_db
class TestMemberUpdate:
    """Тесты обновления роли участника."""

    def test_update_role_as_owner(self, owner_client, test_organization, member_user):
        """Владелец может изменить роль участника."""
        member = OrganizationMember.objects.get(
            organization=test_organization,
            user=member_user,
        )
        url = reverse(
            "api:organization-member-detail",
            kwargs={"organization_id": test_organization.id, "member_id": member.id},
        )
        data = {"role": "admin"}

        response = owner_client.patch(url, data, format="json")

        assert response.status_code == 200
        assert response.data["role"] == "admin"

    def test_update_role_as_admin(self, admin_client, test_organization, member_user):
        """Админ не может изменить роль участника."""
        member = OrganizationMember.objects.get(
            organization=test_organization,
            user=member_user,
        )
        url = reverse(
            "api:organization-member-detail",
            kwargs={"organization_id": test_organization.id, "member_id": member.id},
        )
        data = {"role": "admin"}

        response = admin_client.patch(url, data, format="json")

        assert response.status_code == 403

    def test_update_last_owner_role(self, owner_client, test_organization, test_user):
        """Нельзя понизить роль последнего владельца."""
        member = OrganizationMember.objects.get(
            organization=test_organization,
            user=test_user,
        )
        url = reverse(
            "api:organization-member-detail",
            kwargs={"organization_id": test_organization.id, "member_id": member.id},
        )
        data = {"role": "member"}

        response = owner_client.patch(url, data, format="json")

        assert response.status_code == 400


@pytest.mark.django_db
class TestMemberDelete:
    """Тесты удаления участников."""

    def test_delete_member_as_owner(self, owner_client, test_organization, member_user):
        """Владелец может удалить участника."""
        member = OrganizationMember.objects.get(
            organization=test_organization,
            user=member_user,
        )
        url = reverse(
            "api:organization-member-detail",
            kwargs={"organization_id": test_organization.id, "member_id": member.id},
        )

        response = owner_client.delete(url)

        assert response.status_code == 204
        assert not OrganizationMember.objects.filter(
            organization=test_organization,
            user=member_user,
        ).exists()

    def test_delete_member_as_admin(self, admin_client, test_organization, member_user):
        """Админ может удалить участника."""
        member = OrganizationMember.objects.get(
            organization=test_organization,
            user=member_user,
        )
        url = reverse(
            "api:organization-member-detail",
            kwargs={"organization_id": test_organization.id, "member_id": member.id},
        )

        response = admin_client.delete(url)

        assert response.status_code == 204

    def test_delete_member_as_member(self, member_client, test_organization, admin_user):
        """Обычный участник не может удалять участников."""
        member = OrganizationMember.objects.get(
            organization=test_organization,
            user=admin_user,
        )
        url = reverse(
            "api:organization-member-detail",
            kwargs={"organization_id": test_organization.id, "member_id": member.id},
        )

        response = member_client.delete(url)

        assert response.status_code == 403

    def test_delete_last_owner(self, owner_client, test_organization, test_user):
        """Нельзя удалить последнего владельца."""
        member = OrganizationMember.objects.get(
            organization=test_organization,
            user=test_user,
        )
        url = reverse(
            "api:organization-member-detail",
            kwargs={"organization_id": test_organization.id, "member_id": member.id},
        )

        response = owner_client.delete(url)

        assert response.status_code == 400
