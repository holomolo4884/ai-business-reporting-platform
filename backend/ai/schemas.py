from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AIInsight(BaseModel):
    """Один инсайт из отчёта."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., description="Заголовок инсайта")
    description: str = Field(..., description="Описание инсайта")
    importance: str = Field(
        ...,
        description="Важность: low, medium, high",
    )

    @field_validator("importance")
    @classmethod
    def validate_importance(cls, v: str) -> str:
        """Нормализует importance к допустимым значениям."""
        v = v.lower().strip()
        if v in ("high", "medium", "low"):
            return v
        return "medium"


class AIRecommendation(BaseModel):
    """Одна рекомендация."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., description="Заголовок рекомендации")
    description: str = Field(..., description="Описание")
    expected_impact: str = Field(
        default="",
        description="Ожидаемый эффект",
    )


class AIReportResponse(BaseModel):
    """Структура ответа от AI."""

    model_config = ConfigDict(extra="allow")  # Разрешаем лишние поля (AI может добавить)

    summary: str = Field(..., description="Краткое резюме отчёта")
    insights: list[AIInsight] = Field(
        default_factory=list,
        description="Список инсайтов",
    )
    recommendations: list[AIRecommendation] = Field(
        default_factory=list,
        description="Список рекомендаций",
    )
    generated_text: str = Field(
        ...,
        description="Полный текст отчёта",
    )

    @field_validator("generated_text", mode="before")
    @classmethod
    def normalize_generated_text(cls, v: Any) -> str:
        """
        Нормализует generated_text.

        AI иногда возвращает его как dict с полем 'text' или
        как список строк. Приводим к строке.
        """
        if isinstance(v, str):
            return v
        if isinstance(v, dict):
            # AI вернул {"text": "..."} — извлекаем text
            return v.get("text", v.get("content", str(v)))
        if isinstance(v, list):
            # AI вернул список строк — объединяем
            return "\n".join(str(item) for item in v)
        return str(v)

    @field_validator("summary", mode="before")
    @classmethod
    def normalize_summary(cls, v: Any) -> str:
        """Нормализует summary к строке."""
        if isinstance(v, str):
            return v
        if isinstance(v, dict):
            return v.get("text", v.get("content", str(v)))
        return str(v)
