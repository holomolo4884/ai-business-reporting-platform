from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from business_data.models import Currency, Expense, Order
from metrics.services import MetricsService
from organizations.models import Organization, OrganizationMember


@pytest.fixture(scope="session")
def django_db_setup():
    """Настройка БД для тестов с переопределением настроек Celery."""
    from django.conf import settings

    # В тестах задачи выполняются синхронно (без Celery worker)
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    # Используем memory:// как брокер для тестов (быстрее)
    settings.CELERY_BROKER_URL = "memory://"
    settings.CELERY_RESULT_BACKEND = "cache+memory://"


@pytest.fixture
def api_client():
    """Клиент для тестирования API."""
    return APIClient()


@pytest.fixture
def test_user(db):
    """Тестовый пользователь."""
    User.objects.filter(email="test@example.com").delete()
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
    User.objects.filter(email="second@example.com").delete()
    return User.objects.create_user(
        email="second@example.com",
        password="secondpassword123",
        username="seconduser",
    )


@pytest.fixture
def member_user(db, test_organization):
    """Пользователь с ролью member в организации."""
    User.objects.filter(email="member@example.com").delete()
    user = User.objects.create_user(
        email="member@example.com",
        password="memberpassword123",
        username="memberuser",
    )
    OrganizationMember.objects.get_or_create(
        organization=test_organization,
        user=user,
        defaults={"role": OrganizationMember.Role.MEMBER},
    )
    return user


@pytest.fixture
def admin_user(db, test_organization):
    """Пользователь с ролью admin в организации."""
    User.objects.filter(email="admin@example.com").delete()
    user = User.objects.create_user(
        email="admin@example.com",
        password="adminpassword123",
        username="adminuser",
    )
    OrganizationMember.objects.get_or_create(
        organization=test_organization,
        user=user,
        defaults={"role": OrganizationMember.Role.ADMIN},
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


@pytest.fixture
def metrics_user(db):
    """Пользователь для тестов метрик."""
    User.objects.filter(email="metrics@example.com").delete()
    return User.objects.create_user(
        email="metrics@example.com",
        password="metricspassword123",
        username="metricsuser",
    )


@pytest.fixture
def metrics_organization(db, metrics_user):
    """Организация для тестов метрик."""
    from organizations.models import Organization, OrganizationMember

    org = Organization.objects.create(
        name="Metrics Test Org",
        description="Organization for metrics testing",
    )
    OrganizationMember.objects.create(
        organization=org,
        user=metrics_user,
        role=OrganizationMember.Role.OWNER,
    )
    return org


@pytest.fixture
def period():
    """Период для тестов: последние 30 дней."""
    now = timezone.now()
    return {
        "start": now - timedelta(days=30),
        "end": now,
    }


@pytest.fixture
def sample_orders(db, metrics_organization, period):
    """Набор тестовых заказов."""
    orders = []

    # 3 оплаченных заказа в периоде
    for i, amount in enumerate([100, 200, 300]):
        orders.append(
            Order.objects.create(
                organization=metrics_organization,
                amount=Decimal(str(amount)),
                currency=Currency.USD,
                status=Order.Status.PAID,
                order_date=period["start"] + timedelta(days=i + 1),
                description=f"Paid order {i + 1}",
            )
        )

    # 1 ожидающий заказ в периоде
    orders.append(
        Order.objects.create(
            organization=metrics_organization,
            amount=Decimal("150"),
            currency=Currency.USD,
            status=Order.Status.PENDING,
            order_date=period["start"] + timedelta(days=5),
            description="Pending order",
        )
    )

    # 1 отменённый заказ в периоде
    orders.append(
        Order.objects.create(
            organization=metrics_organization,
            amount=Decimal("50"),
            currency=Currency.USD,
            status=Order.Status.CANCELLED,
            order_date=period["start"] + timedelta(days=6),
            description="Cancelled order",
        )
    )

    # 1 заказ вне периода (100 дней назад — не попадёт ни в текущий, ни в предыдущий)
    orders.append(
        Order.objects.create(
            organization=metrics_organization,
            amount=Decimal("999"),
            currency=Currency.USD,
            status=Order.Status.PAID,
            order_date=period["start"] - timedelta(days=100),
            description="Order outside period",
        )
    )

    return orders


@pytest.fixture
def sample_expenses(db, metrics_organization, period):
    """Набор тестовых расходов."""
    expenses = []

    # Расходы по категориям
    expense_data = [
        (Expense.Category.RENT, 1000),
        (Expense.Category.SALARY, 5000),
        (Expense.Category.MARKETING, 500),
        (Expense.Category.MARKETING, 300),
        (Expense.Category.SOFTWARE, 200),
    ]

    for i, (category, amount) in enumerate(expense_data):
        expenses.append(
            Expense.objects.create(
                organization=metrics_organization,
                amount=Decimal(str(amount)),
                currency=Currency.USD,
                category=category,
                expense_date=period["start"] + timedelta(days=i + 1),
                description=f"Expense {i + 1}",
            )
        )

    # Расход вне периода (не должен попасть в метрики)
    expenses.append(
        Expense.objects.create(
            organization=metrics_organization,
            amount=Decimal("9999"),
            currency=Currency.USD,
            category=Expense.Category.OTHER,
            expense_date=period["start"] - timedelta(days=5),
            description="Expense outside period",
        )
    )

    return expenses


@pytest.fixture
def metrics_service(metrics_organization, period):
    """Экземпляр MetricsService для тестов."""
    return MetricsService(
        organization=metrics_organization,
        period_start=period["start"],
        period_end=period["end"],
    )


@pytest.fixture(scope="session", autouse=True)
def set_fake_ai_provider():
    """В тестах всегда используем FakeAIProvider."""
    from django.conf import settings

    original_provider = getattr(settings, "AI_PROVIDER", "fake")
    settings.AI_PROVIDER = "fake"
    yield
    settings.AI_PROVIDER = original_provider
