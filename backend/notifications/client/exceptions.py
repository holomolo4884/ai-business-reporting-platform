class NotificationError(Exception):
    """Базовое исключение для уведомлений."""


class NotificationServiceUnavailableError(NotificationError):
    """Notification-service недоступен."""


class NotificationAuthenticationError(NotificationError):
    """Ошибка аутентификации в notification-service."""


class NotificationValidationError(NotificationError):
    """Ошибка валидации данных уведомления."""


class NotificationSendError(NotificationError):
    """Ошибка при отправке уведомления."""
