from rest_framework import serializers

from business_data.models import Expense, Order


class OrderSerializer(serializers.ModelSerializer):
    """Serializer для получения данных заказа."""

    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
    )

    class Meta:
        model = Order
        fields = (
            "id",
            "organization",
            "organization_name",
            "amount",
            "currency",
            "status",
            "description",
            "order_date",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer для создания заказа."""

    class Meta:
        model = Order
        fields = (
            "organization",
            "amount",
            "currency",
            "status",
            "description",
            "order_date",
        )

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Сумма должна быть положительной.")
        return value


class OrderUpdateSerializer(serializers.ModelSerializer):
    """Serializer для обновления заказа."""

    class Meta:
        model = Order
        fields = (
            "amount",
            "currency",
            "status",
            "description",
            "order_date",
        )

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Сумма должна быть положительной.")
        return value


class ExpenseSerializer(serializers.ModelSerializer):
    """Serializer для получения данных расхода."""

    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
    )

    class Meta:
        model = Expense
        fields = (
            "id",
            "organization",
            "organization_name",
            "amount",
            "currency",
            "category",
            "description",
            "expense_date",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class ExpenseCreateSerializer(serializers.ModelSerializer):
    """Serializer для создания расхода."""

    class Meta:
        model = Expense
        fields = (
            "organization",
            "amount",
            "currency",
            "category",
            "description",
            "expense_date",
        )

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Сумма должна быть положительной.")
        return value


class ExpenseUpdateSerializer(serializers.ModelSerializer):
    """Serializer для обновления расхода."""

    class Meta:
        model = Expense
        fields = (
            "amount",
            "currency",
            "category",
            "description",
            "expense_date",
        )

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive.")
        return value
