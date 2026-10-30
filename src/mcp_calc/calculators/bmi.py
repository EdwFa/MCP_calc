from pydantic import Field

from mcp_calc.formatting import format_rounded
from mcp_calc.models import CalculatorResult, InputModel
from mcp_calc.results import make_result


class BmiInput(InputModel):
    weight_kg: float = Field(gt=0, le=400)
    height_cm: float = Field(ge=40, le=250)


def bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "недостаточная масса тела"
    if bmi < 25:
        return "нормальная масса тела"
    if bmi < 30:
        return "избыточная масса тела"
    if bmi < 35:
        return "ожирение I степени"
    if bmi < 40:
        return "ожирение II степени"
    return "ожирение III степени"


def compute_bmi(data: BmiInput) -> CalculatorResult:
    raw = data.weight_kg / (data.height_cm / 100) ** 2
    shown, _ = format_rounded(raw, 1)
    return make_result(
        "bmi",
        precise=shown,
        digits=1,
        unit="кг/м²",
        interpretation=f"Категория WHO: {bmi_category(shown)}.",
        inputs=data,
    )
