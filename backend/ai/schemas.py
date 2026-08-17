from pydantic import BaseModel, Field


class AIInsight(BaseModel):
    """Один инсайт из отчёта."""

    title: str = Field(..., description="Заголовок инсайта")
    description: str = Field(..., description="Описание инсайта")
    importance: str = Field(
        ...,
        description="Важность: low, medium, high",
    )


class AIRecommendation(BaseModel):
    """Одна рекомендация."""

    title: str = Field(..., description="Заголовок рекомендации")
    description: str = Field(..., description="Описание")
    expected_impact: str = Field(
        ...,
        description="Ожидаемый эффект",
    )


class AIReportResponse(BaseModel):
    """Структура ответа от AI."""

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

    class Config:
        extra = "forbid"  # Запрещаем лишние поля
