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
        """Создаёт demo организацию и добавляет пользователя как владельца."""
        from organizations.models import Organization, OrganizationMember

        name = "Demo Company"
        description = "Демо-организация для разработки и тестирования"

        organization, created = Organization.objects.get_or_create(
            name=name,
            defaults={
                "description": description,
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"  Создана организация: {name}"))
        else:
            self.stdout.write(f"  Организация уже существует: {name}")

        # Добавляем пользователя как владельца
        member, member_created = OrganizationMember.objects.get_or_create(
            organization=organization,
            user=user,
            defaults={
                "role": OrganizationMember.Role.OWNER,
            },
        )

        if member_created:
            self.stdout.write(f"  Пользователь {user.email} добавлен как владелец")
        else:
            self.stdout.write(f"  Пользователь {user.email} уже является участником")

        return organization

    def _generate_orders(self, organization, count, days):
        """Генерирует заказы."""
        from datetime import timedelta

        from django.utils import timezone

        from business_data.models import Currency, Order

        if organization is None:
            self.stdout.write(self.style.WARNING("  Организация не найдена, пропускаем заказы"))
            return

        self.stdout.write(f"  Генерируем {count} заказов...")

        now = timezone.now()
        orders = []

        statuses = [
            Order.Status.PAID,
            Order.Status.PAID,
            Order.Status.PAID,
            Order.Status.PENDING,
            Order.Status.CANCELLED,
            Order.Status.REFUNDED,
        ]

        currencies = [
            Currency.USD,
            Currency.USD,
            Currency.USD,
            Currency.EUR,
            Currency.RUB,
        ]

        for _ in range(count):
            # Случайная дата за последние N дней
            random_days = self.fake.random_int(min=0, max=days)
            random_hours = self.fake.random_int(min=0, max=23)
            order_date = now - timedelta(days=random_days, hours=random_hours)

            order = Order(
                organization=organization,
                amount=self.fake.pydecimal(
                    left_digits=4,
                    right_digits=2,
                    positive=True,
                    min_value=10,
                    max_value=5000,
                ),
                currency=self.fake.random_element(currencies),
                status=self.fake.random_element(statuses),
                description=self.fake.sentence(nb_words=6),
                order_date=order_date,
            )
            orders.append(order)

        Order.objects.bulk_create(orders)
        self.stdout.write(self.style.SUCCESS(f"  Создано заказов: {len(orders)}"))

    def _generate_expenses(self, organization, count, days):
        """Генерирует расходы."""
        from datetime import timedelta

        from django.utils import timezone

        from business_data.models import Currency, Expense

        if organization is None:
            self.stdout.write(self.style.WARNING("  Организация не найдена, пропускаем расходы"))
            return

        self.stdout.write(f"  Генерируем {count} расходов...")

        now = timezone.now()
        expenses = []

        # Диапазоны сумм для каждой категории
        category_ranges = {
            Expense.Category.RENT: (1000, 5000),
            Expense.Category.SALARY: (5000, 50000),
            Expense.Category.MARKETING: (100, 5000),
            Expense.Category.UTILITIES: (100, 1000),
            Expense.Category.EQUIPMENT: (500, 10000),
            Expense.Category.SOFTWARE: (50, 500),
            Expense.Category.TRAVEL: (200, 5000),
            Expense.Category.OTHER: (50, 2000),
        }

        # Категории с разной частотой появления
        categories = [
            Expense.Category.RENT,
            Expense.Category.SALARY,
            Expense.Category.MARKETING,
            Expense.Category.MARKETING,
            Expense.Category.UTILITIES,
            Expense.Category.SOFTWARE,
            Expense.Category.SOFTWARE,
            Expense.Category.TRAVEL,
            Expense.Category.EQUIPMENT,
            Expense.Category.OTHER,
        ]

        for _ in range(count):
            # Случайная дата за последние N дней
            random_days = self.fake.random_int(min=0, max=days)
            random_hours = self.fake.random_int(min=0, max=23)
            expense_date = now - timedelta(days=random_days, hours=random_hours)

            # Случайная категория
            category = self.fake.random_element(categories)

            # Сумма в зависимости от категории
            min_amount, max_amount = category_ranges[category]

            # Расчёт правильного количества цифр слева
            max_len = max(len(str(int(min_amount))), len(str(int(max_amount))))

            amount = self.fake.pydecimal(
                left_digits=max_len,
                right_digits=2,
                positive=True,
                min_value=min_amount,
                max_value=max_amount,
            )

            expense = Expense(
                organization=organization,
                amount=amount,
                currency=Currency.USD,
                category=category,
                description=self.fake.sentence(nb_words=5),
                expense_date=expense_date,
            )
            expenses.append(expense)

        Expense.objects.bulk_create(expenses)
        self.stdout.write(self.style.SUCCESS(f"  Создано расходов: {len(expenses)}"))
