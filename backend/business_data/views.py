from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from business_data.filters import ExpenseFilter, OrderFilter
from business_data.models import Expense, Order
from business_data.serializers import (
    ExpenseCreateSerializer,
    ExpenseSerializer,
    ExpenseUpdateSerializer,
    OrderCreateSerializer,
    OrderSerializer,
    OrderUpdateSerializer,
)
from organizations.models import OrganizationMember


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet для управления заказами."""

    permission_classes = [IsAuthenticated]
    filterset_class = OrderFilter
    ordering_fields = ["order_date", "amount", "created_at"]
    ordering = ["-order_date"]

    def get_queryset(self):
        # Защита для генерации OpenAPI схемы
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        # Пользователь видит только заказы своих организаций
        return (
            Order.objects.filter(organization__members__user=self.request.user)
            .distinct()
            .select_related("organization")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        if self.action in ("update", "partial_update"):
            return OrderUpdateSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        organization = serializer.validated_data["organization"]

        # Проверяем, что пользователь является участником организации
        if not OrganizationMember.objects.filter(
            organization=organization,
            user=self.request.user,
        ).exists():
            raise PermissionDenied("Вы не являетесь членом этой организации.")

        serializer.save()


class ExpenseViewSet(viewsets.ModelViewSet):
    """ViewSet для управления расходами."""

    permission_classes = [IsAuthenticated]
    filterset_class = ExpenseFilter
    ordering_fields = ["expense_date", "amount", "created_at"]
    ordering = ["-expense_date"]

    def get_queryset(self):
        # Защита для генерации OpenAPI схемы
        if getattr(self, "swagger_fake_view", False):
            return Expense.objects.none()
        return (
            Expense.objects.filter(organization__members__user=self.request.user)
            .distinct()
            .select_related("organization")
        )

    def get_serializer_class(self):
        if self.action == "create":
            return ExpenseCreateSerializer
        if self.action in ("update", "partial_update"):
            return ExpenseUpdateSerializer
        return ExpenseSerializer

    def perform_create(self, serializer):
        organization = serializer.validated_data["organization"]

        # Проверяем, что пользователь является участником организации
        if not OrganizationMember.objects.filter(
            organization=organization,
            user=self.request.user,
        ).exists():
            raise PermissionDenied("Вы не являетесь членом этой организации.")

        serializer.save()
