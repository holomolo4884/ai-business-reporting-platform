import django_filters

from business_data.models import Currency, Expense, Order


class OrderFilter(django_filters.FilterSet):
    """Фильтр для заказов."""

    status = django_filters.ChoiceFilter(choices=Order.Status.choices)
    currency = django_filters.ChoiceFilter(choices=Currency.choices)
    date_from = django_filters.DateTimeFilter(
        field_name="order_date",
        lookup_expr="gte",
        label="Order date from",
    )
    date_to = django_filters.DateTimeFilter(
        field_name="order_date",
        lookup_expr="lte",
        label="Order date to",
    )
    min_amount = django_filters.NumberFilter(
        field_name="amount",
        lookup_expr="gte",
        label="Minimum amount",
    )
    max_amount = django_filters.NumberFilter(
        field_name="amount",
        lookup_expr="lte",
        label="Maximum amount",
    )
    organization = django_filters.NumberFilter(
        field_name="organization_id",
        label="Organization ID",
    )

    class Meta:
        model = Order
        fields = [
            "status",
            "currency",
            "organization",
            "date_from",
            "date_to",
            "min_amount",
            "max_amount",
        ]


class ExpenseFilter(django_filters.FilterSet):
    """Фильтр для расходов."""

    category = django_filters.ChoiceFilter(choices=Expense.Category.choices)
    currency = django_filters.ChoiceFilter(choices=Currency.choices)
    date_from = django_filters.DateTimeFilter(
        field_name="expense_date",
        lookup_expr="gte",
        label="Expense date from",
    )
    date_to = django_filters.DateTimeFilter(
        field_name="expense_date",
        lookup_expr="lte",
        label="Expense date to",
    )
    min_amount = django_filters.NumberFilter(
        field_name="amount",
        lookup_expr="gte",
        label="Minimum amount",
    )
    max_amount = django_filters.NumberFilter(
        field_name="amount",
        lookup_expr="lte",
        label="Maximum amount",
    )
    organization = django_filters.NumberFilter(
        field_name="organization_id",
        label="Organization ID",
    )

    class Meta:
        model = Expense
        fields = [
            "category",
            "currency",
            "organization",
            "date_from",
            "date_to",
            "min_amount",
            "max_amount",
        ]
