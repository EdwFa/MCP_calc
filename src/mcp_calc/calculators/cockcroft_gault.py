from pydantic import Field

from mcp_calc.domain import CREATININE_UMOL_PER_MG_DL, CreatinineUnit, Sex, require_creatinine_mg_dl
from mcp_calc.formatting import format_rounded
from mcp_calc.models import CalculatorResult, Component, InputModel
from mcp_calc.results import make_result


class CockcroftGaultInput(InputModel):
    age_years: int = Field(ge=18, le=120)
    sex: Sex
    weight_kg: float = Field(gt=0, le=400)
    creatinine: float = Field(gt=0, le=4000)
    creatinine_unit: CreatinineUnit


def cockcroft_gault_value(age_years: int, sex: Sex, weight_kg: float, creatinine_mg_dl: float) -> float:
    sex_factor = 0.85 if sex == Sex.female else 1.0
    return ((140 - age_years) * weight_kg * sex_factor) / (72 * creatinine_mg_dl)


def clearance_band(clearance: float) -> str:
    if clearance >= 90:
        return "≥90 мл/мин"
    if clearance >= 60:
        return "60–89 мл/мин"
    if clearance >= 30:
        return "30–59 мл/мин"
    if clearance >= 15:
        return "15–29 мл/мин"
    return "<15 мл/мин"


def compute_cockcroft_gault(data: CockcroftGaultInput) -> CalculatorResult:
    creatinine_mg_dl = require_creatinine_mg_dl(data.creatinine, data.creatinine_unit)
    raw = cockcroft_gault_value(data.age_years, data.sex, data.weight_kg, creatinine_mg_dl)
    shown, _ = format_rounded(raw, 1)
    creatinine_umol = creatinine_mg_dl * CREATININE_UMOL_PER_MG_DL
    sex_factor = 0.85 if data.sex == Sex.female else 1.0
    return make_result(
        "cockcroft_gault",
        precise=shown,
        digits=1,
        unit="мл/мин",
        interpretation=(
            f"Ориентир для дозирования: {clearance_band(shown)}. "
            "Это не стадия CKD по KDIGO и не СКФ, нормированная на площадь тела."
        ),
        inputs=data,
        components=[
            Component(
                label="Креатинин в уравнении",
                value=f"{creatinine_mg_dl:.3f} мг/дл ({creatinine_umol:.1f} мкмоль/л)",
            ),
            Component(label="Коэффициент пола", value=f"{sex_factor:g}"),
        ],
    )
