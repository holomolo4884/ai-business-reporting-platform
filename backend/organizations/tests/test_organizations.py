import pytest
from django.urls import reverse

from organizations.models import Organization, OrganizationMember


@pytest.mark.django_db
class TestOrganizationList:
    """Тесты списка организаций."""

    def test_list_organizations_success(self, owner_client, test_organization):
        """Владелец видит свою организацию."""
        url = reverse("api:organization-list-create")

        response = owner_client.get(url)

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["name"] == test_organization.name
        assert response.data[0]["user_role"] == "owner"

    def test_list_organizations_empty(self, outsider_client):
        """Пользователь без организаций видит пустой список."""
        url = reverse("api:organization-list-create")

        response = outsider_client.get(url)

        assert response.status_code == 200
        assert len(response.data) == 0

    def test_list_organizations_unauthenticated(self, api_client):
        """Неаутентифицированный пользователь получает 401."""
        url = reverse("api:organization-list-create")

        response = api_client.get(url)

        assert response.status_code == 401


@pytest.mark.django_db
class TestOrganizationCreate:
    """Тесты создания организации."""

    def test_create_organization_success(self, owner_client):
        """Успешное создание организации."""
        url = reverse("api:organization-list-create")
        data = {
            "name": "New Organization",
            "description": "A new organization",
        }

        response = owner_client.post(url, data, format="json")

        assert response.status_code == 201
        assert response.data["name"] == "New Organization"
        assert response.data["members_count"] == 1
        assert response.data["user_role"] == "owner"

    def test_create_organization_auto_assigns_owner(self, owner_client, test_user):
        """Создатель автоматически становится владельцем."""
        url = reverse("api:organization-list-create")
        data = {"name": "Auto Owner Org"}

        response = owner_client.post(url, data, format="json")
        org_id = response.data["id"]

        # Проверяем, что создатель добавлен как владелец
        membership = OrganizationMember.objects.get(
            organization_id=org_id,
            user=test_user,
        )
        assert membership.role == OrganizationMember.Role.OWNER

    def test_create_organization_without_name(self, owner_client):
        """Создание без имени должно вернуть ошибку."""
        url = reverse("api:organization-list-create")
        data = {"description": "No name provided"}

        response = owner_client.post(url, data, format="json")

        assert response.status_code == 400
        assert "name" in response.data


@pytest.mark.django_db
class TestOrganizationDetail:
    """Тесты деталей организации."""

    def test_get_organization_detail(self, owner_client, test_organization):
        """Владелец может получить детали организации."""
        url = reverse("api:organization-detail", kwargs={"organization_id": test_organization.id})

        response = owner_client.get(url)

        assert response.status_code == 200
        assert response.data["name"] == test_organization.name

    def test_get_organization_detail_as_outsider(self, outsider_client, test_organization):
        """Пользователь вне организации не может получить детали."""
        url = reverse("api:organization-detail", kwargs={"organization_id": test_organization.id})

        response = outsider_client.get(url)

        assert response.status_code == 403

    def test_update_organization_as_owner(self, owner_client, test_organization):
        """Владелец может обновить организацию."""
        url = reverse("api:organization-detail", kwargs={"organization_id": test_organization.id})
        data = {"name": "Updated Name"}

        response = owner_client.patch(url, data, format="json")

        assert response.status_code == 200
        assert response.data["name"] == "Updated Name"

    def test_update_organization_as_admin(self, admin_client, test_organization):
        """Админ может обновить организацию."""
        url = reverse("api:organization-detail", kwargs={"organization_id": test_organization.id})
        data = {"name": "Updated by Admin"}

        response = admin_client.patch(url, data, format="json")

        assert response.status_code == 200
        assert response.data["name"] == "Updated by Admin"

    def test_update_organization_as_member(self, member_client, test_organization):
        """Обычный участник не может обновить организацию."""
        url = reverse("api:organization-detail", kwargs={"organization_id": test_organization.id})
        data = {"name": "Should Not Work"}

        response = member_client.patch(url, data, format="json")

        assert response.status_code == 403

    def test_delete_organization_as_owner(self, owner_client, test_organization):
        """Владелец может удалить организацию."""
        url = reverse("api:organization-detail", kwargs={"organization_id": test_organization.id})

        response = owner_client.delete(url)

        assert response.status_code == 204
        assert not Organization.objects.filter(id=test_organization.id).exists()

    def test_delete_organization_as_admin(self, admin_client, test_organization):
        """Админ не может удалить организацию."""
        url = reverse("api:organization-detail", kwargs={"organization_id": test_organization.id})

        response = admin_client.delete(url)

        assert response.status_code == 403

    def test_delete_organization_as_member(self, member_client, test_organization):
        """Обычный участник не может удалить организацию."""
        url = reverse("api:organization-detail", kwargs={"organization_id": test_organization.id})

        response = member_client.delete(url)

        assert response.status_code == 403
