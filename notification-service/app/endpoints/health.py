from fastapi import APIRouter

from app.config import settings
from app.schemas.notification import HealthResponse

router = APIRouter()


@router.get("/health/", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Возвращает статус сервиса.
    Используется для мониторинга и оркестрации.
    """
    return HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        version="1.0.0",
    )
