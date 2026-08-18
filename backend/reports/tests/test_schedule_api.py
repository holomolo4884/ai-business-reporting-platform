import pytest
from django.urls import reverse
from rest_framework import status

from reports.models import Report, ReportSchedule


@pytest.fixture
def schedule(db, test_organization, test_user):
    """Создаёт расписание напрямую через ORM для тестов."""
    return ReportSchedule.objects.create(
        organization=test_organization,
        report_type=Report.ReportType.SALES,
        frequency=ReportSchedule.Frequency.DAILY,
        run_at_hour=9,
        run_at_minute=0,
        is_active=True,
        created_by=test_user,
    )


@pytest.mark.django_db
class TestReportScheduleListCreateAPI:
    """Тесты GET/POST /api/v1/organizations/{id}/schedules/"""

    def test_list_schedules_as_owner(self, owner_client, test_organization):
        """Владелец видит список расписаний."""
        url = reverse(
            "api:schedule-list-create",
            kwargs={"organization_id": test_organization.id},
        )
        response = owner_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_list_schedules_as_member(self, member_client, test_organization):
        """Участник видит список расписаний."""
        url = reverse(
            "api:schedule-list-create",
            kwargs={"organization_id": test_organization.id},
        )
        response = member_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_list_schedules_as_outsider(self, outsider_client, test_organization):
        """Чужой не имеет доступа."""
        url = reverse(
            "api:schedule-list-create",
            kwargs={"organization_id": test_organization.id},
        )
        response = outsider_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_daily_schedule_as_owner(self, owner_client, test_organization):
        """Владелец создаёт daily расписание."""
        url = reverse(
            "api:schedule-list-create",
            kwargs={"organization_id": test_organization.id},
        )
        data = {
            "report_type": "sales",
            "frequency": "daily",
            "run_at_hour": 9,
            "run_at_minute": 0,
        }
        response = owner_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["frequency"] == "daily"
        assert response.data["organization"] == test_organization.id
        assert response.data["is_active"] is True
        assert response.data["next_run_at"] is not None

    def test_create_weekly_schedule(self, owner_client, test_organization):
        """Создание weekly расписания."""
        url = reverse(
            "api:schedule-list-create",
            kwargs={"organization_id": test_organization.id},
        )
        data = {
            "report_type": "sales",
            "frequency": "weekly",
            "run_day_of_week": 0,
            "run_at_hour": 10,
        }
        response = owner_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["frequency"] == "weekly"
        assert response.data["run_day_of_week"] == 0

    def test_create_monthly_schedule(self, owner_client, test_organization):
        """Создание monthly расписания."""
        url = reverse(
            "api:schedule-list-create",
            kwargs={"organization_id": test_organization.id},
        )
        data = {
            "report_type": "finance",
            "frequency": "monthly",
            "run_day_of_month": 1,
            "run_at_hour": 8,
        }
        response = owner_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["frequency"] == "monthly"
        assert response.data["run_day_of_month"] == 1

    def test_create_schedule_as_member_fails(self, member_client, test_organization):
        """Участник не может создавать расписания."""
        url = reverse(
            "api:schedule-list-create",
            kwargs={"organization_id": test_organization.id},
        )
        data = {
            "report_type": "sales",
            "frequency": "daily",
        }
        response = member_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_duplicate_schedule_fails(self, owner_client, test_organization):
        """Нельзя создать два одинаковых расписания."""
        url = reverse(
            "api:schedule-list-create",
            kwargs={"organization_id": test_organization.id},
        )
        data = {
            "report_type": "sales",
            "frequency": "daily",
        }

        # Первый раз — успешно
        response1 = owner_client.post(url, data, format="json")
        assert response1.status_code == status.HTTP_201_CREATED

        # Второй раз — ошибка
        response2 = owner_client.post(url, data, format="json")
        assert response2.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestReportScheduleDetailAPI:
    """Тесты GET/PATCH/DELETE /api/v1/schedules/{id}/"""

    def test_get_schedule_as_owner(self, owner_client, schedule):
        """Владелец получает детали."""
        url = reverse("api:schedule-detail", kwargs={"schedule_id": schedule.id})
        response = owner_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == schedule.id
        assert response.data["frequency"] == "daily"

    def test_get_schedule_as_member(self, member_client, schedule):
        """Участник получает детали."""
        url = reverse("api:schedule-detail", kwargs={"schedule_id": schedule.id})
        response = member_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_get_schedule_as_outsider(self, outsider_client, schedule):
        """Чужой не имеет доступа."""
        url = reverse("api:schedule-detail", kwargs={"schedule_id": schedule.id})
        response = outsider_client.get(url)

        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ]

    def test_update_schedule_as_owner(self, owner_client, schedule):
        """Владелец обновляет расписание."""
        url = reverse("api:schedule-detail", kwargs={"schedule_id": schedule.id})
        data = {"run_at_hour": 10, "is_active": False}
        response = owner_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["run_at_hour"] == 10
        assert response.data["is_active"] is False

    def test_update_schedule_as_member_fails(self, member_client, schedule):
        """Участник не может обновлять."""
        url = reverse("api:schedule-detail", kwargs={"schedule_id": schedule.id})
        data = {"run_at_hour": 11}
        response = member_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_schedule_as_owner(self, owner_client, schedule):
        """Владелец удаляет расписание."""
        url = reverse("api:schedule-detail", kwargs={"schedule_id": schedule.id})
        response = owner_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ReportSchedule.objects.filter(id=schedule.id).exists()

    def test_delete_schedule_as_member_fails(self, member_client, schedule):
        """Участник не может удалять."""
        url = reverse("api:schedule-detail", kwargs={"schedule_id": schedule.id})
        response = member_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_nonexistent_schedule_fails(self, owner_client):
        """Несуществующее расписание возвращает 404."""
        url = reverse("api:schedule-detail", kwargs={"schedule_id": 99999})
        response = owner_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
