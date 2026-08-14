from django.urls import include, path
from rest_framework.routers import DefaultRouter

from business_data.views import ExpenseViewSet, OrderViewSet

router = DefaultRouter()
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"expenses", ExpenseViewSet, basename="expense")

urlpatterns = [
    path("", include(router.urls)),
]
