from typing import Any

from pydantic import BaseModel, ConfigDict, Field


DISCLAIMER = (
    "Результат получен по опубликованной формуле и предназначен только для обучения "
    "и демонстрации. Он не является диагнозом, медицинской рекомендацией и не заменяет консультацию врача."
)


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Component(BaseModel):
    label: str
    value: str


class CalculatorResult(BaseModel):
    calculator_id: str
    name: str
    value: float
    value_display: str
    unit: str
    interpretation: str
    formula: str
    reference: str
    inputs_used: dict[str, Any]
    components: list[Component] = Field(default_factory=list)
    disclaimer: str = DISCLAIMER
