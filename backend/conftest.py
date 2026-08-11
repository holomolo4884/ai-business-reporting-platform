import pytest
from rest_framework.test import APIClient

from accounts.models import User
from organizations.models import Organization, OrganizationMember


@pytest.fixture
def api_client():
    """Клиент для тестирования API."""
    return APIClient()


@pytest.fixture
def test_user(db):
    """Тестовый пользователь."""
    return User.objects.create_user(
        email="test@example.com",
        password="testpassword123",
        username="testuser",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def authenticated_client(api_client, test_user):
    """Аутентифицированный клиент с JWT токеном."""
    response = api_client.post(
        "/api/v1/auth/token/",
        {"email": test_user.email, "password": "testpassword123"},
        format="json",
    )
    access_token = response.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    return api_client


@pytest.fixture
def test_organization(db, test_user):
    """Тестовая организация с владельцем."""
    org = Organization.objects.create(
        name="Test Organization",
        description="A test organization",
    )
    OrganizationMember.objects.create(
        organization=org,
        user=test_user,
        role=OrganizationMember.Role.OWNER,
    )
    return org


@pytest.fixture
def second_user(db):
    """Второй тестовый пользователь."""
    return User.objects.create_user(
        email="second@example.com",
        password="secondpassword123",
        username="seconduser",
    )


@pytest.fixture
def member_user(db, test_organization):
    """Пользователь с ролью member в организации."""
    user = User.objects.create_user(
        email="member@example.com",
        password="memberpassword123",
        username="memberuser",
    )
    OrganizationMember.objects.create(
        organization=test_organization,
        user=user,
        role=OrganizationMember.Role.MEMBER,
    )
    return user


@pytest.fixture
def admin_user(db, test_organization):
    """Пользователь с ролью admin в организации."""
    user = User.objects.create_user(
        email="admin@example.com",
        password="adminpassword123",
        username="adminuser",
    )
    OrganizationMember.objects.create(
        organization=test_organization,
        user=user,
        role=OrganizationMember.Role.ADMIN,
    )
    return user


@pytest.fixture
def owner_client(api_client, test_user):
    """Аутентифицированный клиент владельца организации."""
    response = api_client.post(
        "/api/v1/auth/token/",
        {"email": test_user.email, "password": "testpassword123"},
        format="json",
    )
    access_token = response.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    return api_client


@pytest.fixture
def member_client(api_client, member_user):
    """Аутентифицированный клиент участника организации."""
    response = api_client.post(
        "/api/v1/auth/token/",
        {"email": member_user.email, "password": "memberpassword123"},
        format="json",
    )
    access_token = response.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Аутентифицированный клиент админа организации."""
    response = api_client.post(
        "/api/v1/auth/token/",
        {"email": admin_user.email, "password": "adminpassword123"},
        format="json",
    )
    access_token = response.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    return api_client


@pytest.fixture
def outsider_client(api_client, second_user):
    """Аутентифицированный клиент пользователя вне организации."""
    response = api_client.post(
        "/api/v1/auth/token/",
        {"email": second_user.email, "password": "secondpassword123"},
        format="json",
    )
    access_token = response.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    return api_client
