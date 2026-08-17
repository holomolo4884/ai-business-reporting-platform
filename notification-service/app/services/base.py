from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SendResult:
    """Результат отправки уведомления."""

    success: bool
    message: str
    error_details: str | None = None


class BaseSender(ABC):
    """Абстрактный базовый класс для отправителей."""

    @abstractmethod
    async def send(
        self,
        recipient: str,
        subject: str,
        message: str,
        metadata: dict | None = None,
    ) -> SendResult:
        """Отправляет уведомление."""
