class AIError(Exception):
    """Базовое исключение для AI."""


class AIServiceUnavailableError(AIError):
    """AI сервис недоступен."""


class AIResponseValidationError(AIError):
    """Ошибка валидации ответа от AI."""


class AITimeoutError(AIError):
    """Превышено время ожидания ответа от AI."""


class AIPromptError(AIError):
    """Ошибка при формировании промпта."""
