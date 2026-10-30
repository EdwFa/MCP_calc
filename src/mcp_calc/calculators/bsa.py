import math

from pydantic import Field

from mcp_calc.formatting import format_rounded
from mcp_calc.models import CalculatorResult, InputModel
from mcp_calc.results import make_result


class BsaInput(InputModel):
    weight_kg: float = Field(gt=0, le=400)
    height_cm: float = Field(ge=40, le=250)


def compute_bsa(data: BsaInput) -> CalculatorResult:
    raw = math.sqrt(data.height_cm * data.weight_kg / 3600)
    shown, _ = format_rounded(raw, 2)
    return make_result(
        "bsa_mosteller",
        precise=shown,
        digits=2,
        unit="м²",
        interpretation="Площадь поверхности тела по Mosteller. У формулы нет диагностических порогов.",
        inputs=data,
    )
