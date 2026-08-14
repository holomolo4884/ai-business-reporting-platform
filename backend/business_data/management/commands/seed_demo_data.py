from django.core.management.base import BaseCommand
from faker import Faker


class Command(BaseCommand):
    help = "Генерация демо-данных для разработки и тестирования"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fake = Faker()

    def add_arguments(self, parser):
        parser.add_argument(
            "--orders",
            type=int,
            default=100,
            help="Количество заказов для генерации (по умолчанию: 100)",
        )
        parser.add_argument(
            "--expenses",
            type=int,
            default=50,
            help="Количество расходов для генерации (по умолчанию: 50)",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="Количество дней для распределения данных (по умолчанию: 90)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Очистить существующие демо-данные перед генерацией",
        )

    def handle(self, *args, **options):
        orders_count = options["orders"]
        expenses_count = options["expenses"]
        days = options["days"]
        clear = options["clear"]

        self.stdout.write(self.style.NOTICE("Начинаем генерацию демо-данных..."))

        if clear:
            self._clear_existing_data()

        # Создаём demo пользователя (G-03)
        user = self._create_demo_user()

        # Создаём demo организацию (G-04)
        organization = self._create_demo_organization(user)

        # Генерируем заказы (G-05)
        self._generate_orders(organization, orders_count, days)

        # Генерируем расходы (G-06)
        self._generate_expenses(organization, expenses_count, days)

        self.stdout.write(self.style.SUCCESS("Генерация демо-данных завершена!"))
        self.stdout.write(f"  Создано заказов: {orders_count}")
        self.stdout.write(f"  Создано расходов: {expenses_count}")
        self.stdout.write(f"  Период: последние {days} дней")

    def _clear_existing_data(self):
        """Очищает существующие демо-данные."""
        from business_data.models import Expense, Order

        orders_deleted = Order.objects.count()
        expenses_deleted = Expense.objects.count()

        Order.objects.all().delete()
        Expense.objects.all().delete()

        self.stdout.write(f"  Удалено заказов: {orders_deleted}")
        self.stdout.write(f"  Удалено расходов: {expenses_deleted}")

    def _create_demo_user(self):
        """Создаёт demo пользователя."""
        from accounts.models import User

        email = "demo@example.com"
        password = "demo123456"
        username = "demo_user"

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": username,
                "first_name": "Demo",
                "last_name": "User",
                "is_active": True,
            },
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"  Создан пользователь: {email}"))
        else:
            self.stdout.write(f"  Пользователь уже существует: {email}")

        self.stdout.write(f"  Email: {email}")
        self.stdout.write(f"  Пароль: {password}")

        return user

    def _create_demo_organization(self, user):
        """Создаёт демо-организацию."""
        # Реализация в G-04
        self.stdout.write("  Создаём демо-организацию...")
        return None

    def _generate_orders(self, organization, count, days):
        """Генерирует заказы."""
        # Реализация в G-05
        self.stdout.write(f"  Генерируем {count} заказов...")

    def _generate_expenses(self, organization, count, days):
        """Генерирует расходы."""
        # Реализация в G-06
        self.stdout.write(f"  Генерируем {count} расходов...")
