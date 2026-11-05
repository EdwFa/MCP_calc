from math import log10

from pydantic import Field

from mcp_calc.domain import Sex
from mcp_calc.formatting import format_rounded
from mcp_calc.models import CalculatorResult, Component, InputModel
from mcp_calc.results import make_result


class BodyFatNavyInput(InputModel):
    sex: Sex
    height_cm: float = Field(ge=100, le=250)
    neck_cm: float = Field(ge=20, le=80)
    waist_cm: float = Field(ge=40, le=200)
    hip_cm: float | None = Field(default=None, ge=50, le=200)


def body_fat_navy_value(
    sex: Sex,
    height_cm: float,
    neck_cm: float,
    waist_cm: float,
    hip_cm: float | None,
) -> float:
    if sex == Sex.male:
        girth = waist_cm - neck_cm
        if girth <= 0:
            raise ValueError("Талия должна быть больше шеи. Проверьте замеры.")
        density = 1.0324 - 0.19077 * log10(girth) + 0.15456 * log10(height_cm)
    else:
        if hip_cm is None:
            raise ValueError("Для женщин нужен обхват бёдер.")
        girth = waist_cm + hip_cm - neck_cm
        if girth <= 0:
            raise ValueError("Талия + бёдра должны быть больше шеи. Проверьте замеры.")
        density = 1.29579 - 0.35004 * log10(girth) + 0.22100 * log10(height_cm)
    return 495 / density - 450


def body_fat_band(percent: float, sex: Sex) -> str:
    limits = (6, 14, 18, 25) if sex == Sex.male else (14, 21, 25, 32)
    labels = ("незаменимый жир", "атлетический уровень", "уровень фитнеса", "средний уровень")
    for limit, label in zip(limits, labels):
        if percent < limit:
            return label
    return "уровень ожирения"


def compute_body_fat_navy(data: BodyFatNavyInput) -> CalculatorResult:
    raw = body_fat_navy_value(data.sex, data.height_cm, data.neck_cm, data.waist_cm, data.hip_cm)
    shown, _ = format_rounded(raw, 1)
    if shown < 2 or shown > 75:
        raise ValueError("Результат вне правдоподобного диапазона 2–75 %. Проверьте замеры.")
    formula_used = "мужская, бёдра не используются" if data.sex == Sex.male else "женская"
    return make_result(
        "body_fat_navy",
        precise=shown,
        digits=1,
        unit="%",
        interpretation=(
            f"Ориентир ACE: {body_fat_band(shown, data.sex)}. "
            "Это оценка всего жира в теле по обхватам, а не только подкожного."
        ),
        inputs=data,
        components=[Component(label="Вариант формулы", value=formula_used)],
    )

