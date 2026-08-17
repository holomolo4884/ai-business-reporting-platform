from fastapi import APIRouter

from app.dependencies import RequireAPIKey
from app.schemas.notification import NotificationRequest, NotificationResponse
from app.services.notification_service import notification_service

router = APIRouter()


@router.post(
    "/notifications/send/",
    response_model=NotificationResponse,
    tags=["Notifications"],
    summary="Отправить уведомление",
    description=(
        "Отправляет уведомление через указанный канал (email, telegram, webhook).\n\n"
        "Требует API ключ в заголовке `X-API-Key`."
    ),
)
async def send_notification(
    request: NotificationRequest,
    _: str = RequireAPIKey,
) -> NotificationResponse:
    """
    Отправить уведомление.

    - **channel**: канал доставки (email, telegram, webhook)
    - **recipient**: получатель (email / chat_id / URL)
    - **subject**: тема (для email)
    - **message**: текст уведомления
    - **priority**: приоритет (low, normal, high)
    - **metadata**: дополнительные данные
    """
    return await notification_service.send(request)
