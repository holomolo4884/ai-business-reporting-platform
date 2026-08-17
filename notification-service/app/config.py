from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Путь к корневому .env (на 2 уровня выше от notification-service/app/)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = ROOT_DIR / ".env"


class Settings(BaseSettings):
    """Настройки приложения."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Игнорируем лишние переменные из общего .env
    )

    # Приложение
    APP_NAME: str = "Notification Service"
    DEBUG: bool = False

    # Сервер
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    # Email настройки (SMTP)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@example.com"
    SMTP_USE_TLS: bool = True

    # Telegram Bot Token
    TELEGRAM_BOT_TOKEN: str = ""

    # Internal API key для вызовов из Django
    # Читается из NOTIFICATION_INTERNAL_API_KEY в .env
    NOTIFICATION_INTERNAL_API_KEY: str = "change-me"

    # CORS
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:8000"

    @property
    def cors_origins_list(self) -> list[str]:
        """Преобразует строку CORS в список."""
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",")]


settings = Settings()
