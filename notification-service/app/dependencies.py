from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from structlog import get_logger

from app.config import settings

logger = get_logger()

# Заголовок для передачи API ключа
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str | None = Security(api_key_header)) -> str:
    """
    Проверяет API ключ из заголовка X-API-Key.

    Используется для защиты внутренних endpoint'ов,
    которые вызываются из Django.
    """
    if not api_key:
        logger.warning("Запрос без API ключа")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key не предоставлен",
        )

    if api_key != settings.NOTIFICATION_INTERNAL_API_KEY:
        logger.warning("Неверный API ключ", key_prefix=api_key[:8] + "...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Неверный API ключ",
        )

    return api_key


# Alias для удобства
RequireAPIKey = Depends(verify_api_key)
