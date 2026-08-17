import json
import logging
import random
import time
from abc import ABC, abstractmethod

from pydantic import ValidationError

from ai.exceptions import (
    AIResponseValidationError,
    AIServiceUnavailableError,
)
from ai.schemas import AIReportResponse

logger = logging.getLogger(__name__)


class BaseAIProvider(ABC):
    """Базовый класс для AI провайдеров."""

    @abstractmethod
    def generate_report(
        self,
        prompt: str,
        report_type: str,
    ) -> dict:
        """Генерирует отчёт на основе промпта."""

    def _extract_json(self, text: str) -> str:
        """
        Извлекает JSON из текста ответа.

        Обрабатывает случаи, когда AI оборачивает JSON в markdown блоки:
        ```json
        {...}
        ```
        """
        text = text.strip()

        # Если текст уже начинается с { — возвращаем как есть
        if text.startswith("{"):
            return text

        # Ищем JSON внутри markdown блоков ```json ... ```
        import re

        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            return match.group(1)

        # Ищем любой объект { ... } в тексте
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return match.group(0)

        return text

    def validate_response(self, response_text: str) -> dict:
        """Валидирует ответ от AI через Pydantic."""
        # Логируем сырой ответ для отладки
        logger.debug("Сырой ответ AI (первые 500 символов): %s", response_text[:500])

        # Извлекаем JSON из возможных markdown блоков
        json_text = self._extract_json(response_text)

        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as err:
            raise AIResponseValidationError(
                f"AI вернул не-JSON ответ: {err}. " f"Сырой ответ: {response_text[:300]}"
            ) from err

        try:
            validated = AIReportResponse.model_validate(data)
            return validated.model_dump()
        except ValidationError as err:
            raise AIResponseValidationError(f"Ответ AI не соответствует схеме: {err}") from err


class FakeAIProvider(BaseAIProvider):
    """
    Фейковый AI провайдер для разработки и тестов.

    Возвращает предсказуемые данные без реальных API вызовов.
    """

    def generate_report(
        self,
        prompt: str,
        report_type: str,
    ) -> dict:
        """Генерирует фейковый отчёт."""
        logger.info("Используется FakeAIProvider для генерации отчёта")

        # Симулируем задержку (как будто думаем)
        time.sleep(random.uniform(0.5, 1.5))

        # Формируем фейковый ответ
        fake_response = {
            "summary": (
                f"Это фейковый отчёт типа '{report_type}', "
                "сгенерированный для разработки. "
                "В продакшене здесь будет реальный анализ от AI."
            ),
            "insights": [
                {
                    "title": "Стабильные продажи",
                    "description": "Количество заказов остаётся на стабильном уровне.",
                    "importance": "medium",
                },
                {
                    "title": "Расходы под контролем",
                    "description": "Основные расходы приходятся на ожидаемые категории.",
                    "importance": "low",
                },
                {
                    "title": "Возможность роста",
                    "description": "Есть потенциал для увеличения среднего чека.",
                    "importance": "high",
                },
            ],
            "recommendations": [
                {
                    "title": "Увеличить маркетинговый бюджет",
                    "description": "Рассмотреть увеличение бюджета на маркетинг на 10%.",
                    "expected_impact": "Рост выручки на 15%",
                },
                {
                    "title": "Оптимизировать расходы",
                    "description": "Пересмотреть подписки на SaaS сервисы.",
                    "expected_impact": "Снижение расходов на 5%",
                },
            ],
            "generated_text": (
                "## Отчёт за период\n\n"
                "За анализируемый период организация продемонстрировала "
                "стабильные результаты. Выручка соответствует ожиданиям, "
                "а расходы находятся в пределах нормы.\n\n"
                "### Ключевые моменты\n\n"
                "Основные продажи приходятся на первую половину периода. "
                "Средний чек показывает положительную динамику. "
                "Распределение расходов по категориям соответствует "
                "отраслевым стандартам.\n\n"
                "### Рекомендации\n\n"
                "Для дальнейшего роста рекомендуется:\n"
                "1. Увеличить маркетинговую активность\n"
                "2. Оптимизировать операционные расходы\n"
                "3. Внедрить программу лояльности для клиентов"
            ),
        }

        # Валидируем ответ (чтобы проверить схему)
        validated = self.validate_response(json.dumps(fake_response))
        return validated


class GigaChatProvider(BaseAIProvider):
    """
    Провайдер для работы с GigaChat API от Сбера.

    Использует официальный Python SDK gigachat.
    """

    def __init__(
        self,
        credentials: str,
        model: str = "GigaChat",
        scope: str = "GIGACHAT_API_PERS",
        verify_ssl_certs: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        self.credentials = credentials
        self.model = model
        self.scope = scope
        self.verify_ssl_certs = verify_ssl_certs
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate_report(
        self,
        prompt: str,
        report_type: str,
    ) -> dict:
        """Генерирует отчёт через GigaChat API."""
        from gigachat import GigaChat
        from gigachat.models import Chat, Messages, MessagesRole

        logger.info(
            "GigaChatProvider: модель %s, scope %s",
            self.model,
            self.scope,
        )

        try:
            with GigaChat(
                credentials=self.credentials,
                model=self.model,
                scope=self.scope,
                verify_ssl_certs=self.verify_ssl_certs,
            ) as client:
                # Формируем запрос с параметрами
                payload = Chat(
                    messages=[
                        Messages(
                            role=MessagesRole.SYSTEM,
                            content=(
                                "Ты — профессиональный бизнес-аналитик. "
                                "Составляй отчёты на русском языке. "
                                "Возвращай ответ ТОЛЬКО в формате JSON."
                            ),
                        ),
                        Messages(
                            role=MessagesRole.USER,
                            content=prompt,
                        ),
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )

                response = client.chat(payload)
                response_text = response.choices[0].message.content
                logger.info(
                    "Получен ответ от GigaChat длиной %d символов",
                    len(response_text),
                )

        except Exception as exc:
            logger.exception("Ошибка при вызове GigaChat API")
            raise AIServiceUnavailableError(f"GigaChat API недоступен: {exc}") from exc

        return self.validate_response(response_text)


def get_ai_provider() -> BaseAIProvider:
    """
    Фабрика для получения AI провайдера.

    Выбор провайдера определяется переменной окружения AI_PROVIDER.
    """
    from django.conf import settings

    provider_name = getattr(settings, "AI_PROVIDER", "fake")

    if provider_name == "fake":
        return FakeAIProvider()

    if provider_name == "gigachat":
        credentials = getattr(settings, "AI_API_KEY", "")
        model = getattr(settings, "AI_MODEL", "GigaChat")
        scope = getattr(settings, "AI_SCOPE", "GIGACHAT_API_PERS")
        verify_ssl = getattr(settings, "AI_VERIFY_SSL", False)
        temperature = getattr(settings, "AI_TEMPERATURE", 0.7)
        max_tokens = getattr(settings, "AI_MAX_TOKENS", 2000)
        return GigaChatProvider(
            credentials=credentials,
            model=model,
            scope=scope,
            verify_ssl_certs=verify_ssl,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    logger.warning(
        "Неизвестный AI провайдер '%s', используем fake",
        provider_name,
    )
    return FakeAIProvider()
