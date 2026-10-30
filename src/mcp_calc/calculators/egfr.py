from pydantic import Field

from mcp_calc.domain import CreatinineUnit, Sex, require_creatinine_mg_dl
from mcp_calc.formatting import format_rounded
from mcp_calc.models import CalculatorResult, Component, InputModel
from mcp_calc.results import make_result


class EgfrInput(InputModel):
    age_years: int = Field(ge=18, le=120)
    sex: Sex
    creatinine: float = Field(gt=0, le=4000)
    creatinine_unit: CreatinineUnit


def gfr_category(gfr: float) -> tuple[str, str]:
    if gfr >= 90:
        return "G1", "высокая или нормальная"
    if gfr >= 60:
        return "G2", "незначительно сниженная"
    if gfr >= 45:
        return "G3a", "сниженная от незначительно до умеренно"
    if gfr >= 30:
        return "G3b", "сниженная от умеренно до существенно"
    if gfr >= 15:
        return "G4", "существенно сниженная"
    return "G5", "в диапазоне почечной недостаточности (<15)"


def egfr_ckd_epi_2021_value(creatinine_mg_dl: float, age_years: int, sex: Sex) -> float:
    if sex == Sex.female:
        kappa = 0.7
        alpha = -0.241
        sex_factor = 1.012
    else:
        kappa = 0.9
        alpha = -0.302
        sex_factor = 1.0
    ratio = creatinine_mg_dl / kappa
    return (
        142
        * min(ratio, 1) ** alpha
        * max(ratio, 1) ** (-1.200)
        * (0.9938**age_years)
        * sex_factor
    )


def compute_egfr(data: EgfrInput) -> CalculatorResult:
    creatinine_mg_dl = require_creatinine_mg_dl(data.creatinine, data.creatinine_unit)
    raw = egfr_ckd_epi_2021_value(creatinine_mg_dl, data.age_years, data.sex)
    shown, _ = format_rounded(raw, 1)
    code, phrase = gfr_category(shown)
    creatinine_umol = creatinine_mg_dl * 88.4
    return make_result(
        "egfr_ckd_epi_2021",
        precise=shown,
        digits=1,
        unit="мл/мин/1,73 м²",
        interpretation=(
            f"Категория {code} по KDIGO: расчётная СКФ {phrase}. "
            "Категория описывает только величину СКФ."
        ),
        inputs=data,
        components=[
            Component(
                label="Креатинин в уравнении",
                value=f"{creatinine_mg_dl:.3f} мг/дл ({creatinine_umol:.1f} мкмоль/л)",
            ),
            Component(label="Категория KDIGO", value=code),
        ],
    )
