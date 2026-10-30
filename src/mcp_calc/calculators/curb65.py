from pydantic import Field

from mcp_calc.formatting import plural_points
from mcp_calc.models import CalculatorResult, Component, InputModel
from mcp_calc.results import make_result


class Curb65Input(InputModel):
    age_years: int = Field(ge=18, le=120)
    confusion: bool
    urea_mmol_l: float = Field(ge=0, le=80)
    respiratory_rate: int = Field(ge=4, le=80)
    systolic_bp: int = Field(ge=40, le=300)
    diastolic_bp: int = Field(ge=20, le=200)


def curb65_rows(data: Curb65Input) -> list[tuple[str, int]]:
    low_bp = data.systolic_bp < 90 or data.diastolic_bp <= 60
    return [
        ("Новое нарушение сознания", 1 if data.confusion else 0),
        ("Мочевина > 7 ммоль/л", 1 if data.urea_mmol_l > 7 else 0),
        ("Частота дыхания ≥ 30", 1 if data.respiratory_rate >= 30 else 0),
        ("САД < 90 или ДАД ≤ 60", 1 if low_bp else 0),
        ("Возраст ≥ 65 лет", 1 if data.age_years >= 65 else 0),
    ]


def curb65_severity(score: int) -> str:
    if score <= 1:
        return "низкая тяжесть"
    if score == 2:
        return "средняя тяжесть"
    return "высокая тяжесть"


def compute_curb65(data: Curb65Input) -> CalculatorResult:
    if data.diastolic_bp > data.systolic_bp:
        raise ValueError("Диастолическое давление не может быть выше систолического.")
    rows = curb65_rows(data)
    score = sum(points for _, points in rows)
    return make_result(
        "curb65",
        precise=float(score),
        digits=0,
        unit=plural_points(score),
        interpretation=(
            f"По CURB-65 это {curb65_severity(score)}. "
            "Стратификация шкалы не является правилом госпитализации."
        ),
        inputs=data,
        components=[Component(label=label, value=str(points)) for label, points in rows],
    )
