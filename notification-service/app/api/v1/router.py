from fastapi import APIRouter

from app.endpoints.health import router as health_router
from app.endpoints.notifications import router as notification_router

router = APIRouter(prefix="/api/v1")

# Подключаем роутеры
router.include_router(health_router)
router.include_router(notification_router)
