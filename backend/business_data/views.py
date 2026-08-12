from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from business_data.models import Expense, Order
from business_data.serializers import (
    ExpenseCreateSerializer,
    ExpenseSerializer,
    ExpenseUpdateSerializer,
    OrderCreateSerializer,
    OrderSerializer,
    OrderUpdateSerializer,
)


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet для управления заказами."""

    permission_classes = [IsAuthenticated]
    ordering_fields = ["order_date", "amount", "created_at"]
    ordering = ["-order_date"]

    def get_queryset(self):
        # Пока возвращаем все заказы.
        # Ограничение по организациям добавим в F-11.
        return Order.objects.select_related("organization")

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        if self.action in ("update", "partial_update"):
            return OrderUpdateSerializer
        return OrderSerializer


class ExpenseViewSet(viewsets.ModelViewSet):
    """ViewSet для управления расходами."""

    permission_classes = [IsAuthenticated]
    ordering_fields = ["expense_date", "amount", "created_at"]
    ordering = ["-expense_date"]

    def get_queryset(self):
        # Пока возвращаем все расходы.
        # Ограничение по организациям добавим в F-11.
        return Expense.objects.select_related("organization")

    def get_serializer_class(self):
        if self.action == "create":
            return ExpenseCreateSerializer
        if self.action in ("update", "partial_update"):
            return ExpenseUpdateSerializer
        return ExpenseSerializer
