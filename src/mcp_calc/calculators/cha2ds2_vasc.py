from pydantic import Field

from mcp_calc.domain import Sex
from mcp_calc.formatting import plural_points
from mcp_calc.models import CalculatorResult, Component, InputModel
from mcp_calc.results import make_result


class Cha2ds2VascInput(InputModel):
    age_years: int = Field(ge=18, le=120)
    sex: Sex
    congestive_heart_failure: bool
    hypertension: bool
    diabetes: bool
    stroke_tia_thromboembolism: bool
    vascular_disease: bool


def cha2ds2_points(data: Cha2ds2VascInput) -> list[tuple[str, int]]:
    if data.age_years >= 75:
        age_75, age_65 = 2, 0
    elif data.age_years >= 65:
        age_75, age_65 = 0, 1
    else:
        age_75, age_65 = 0, 0
    return [
        ("Хроническая сердечная недостаточность", 1 if data.congestive_heart_failure else 0),
        ("Артериальная гипертензия", 1 if data.hypertension else 0),
        ("Возраст ≥75 лет", age_75),
        ("Сахарный диабет", 1 if data.diabetes else 0),
        ("Инсульт, ТИА или тромбоэмболия", 2 if data.stroke_tia_thromboembolism else 0),
        ("Сосудистое заболевание", 1 if data.vascular_disease else 0),
        ("Возраст 65–74 года", age_65),
        ("Женский пол", 1 if data.sex == Sex.female else 0),
    ]


def cha2ds2_band(score: int, sex: Sex) -> str:
    if sex == Sex.male:
        if score == 0:
            return "низкая категория для мужчины (0 баллов)"
        if score == 1:
            return "промежуточная категория для мужчины (1 балл)"
        return "высокая категория для мужчины (2 балла и больше)"
    if score <= 1:
        return "низкая категория для женщины (0–1 балл, один балл может давать только пол)"
    if score == 2:
        return "промежуточная категория для женщины (2 балла)"
    return "высокая категория для женщины (3 балла и больше)"


def compute_cha2ds2_vasc(data: Cha2ds2VascInput) -> CalculatorResult:
    rows = cha2ds2_points(data)
    score = sum(points for _, points in rows)
    return make_result(
        "cha2ds2_vasc",
        precise=float(score),
        digits=0,
        unit=plural_points(score),
        interpretation=(
            f"По порогам CHA₂DS₂-VASc это {cha2ds2_band(score, data.sex)}. "
            "Это учебная справка по шкале, а не назначение антикоагулянта."
        ),
        inputs=data,
        components=[Component(label=label, value=str(points)) for label, points in rows],
    )
