from pydantic import BaseModel

from mcp_calc.formatting import format_rounded
from mcp_calc.models import CalculatorResult, Component
from mcp_calc.registry import get_calculator


def make_result(
    calculator_id: str,
    *,
    precise: float,
    digits: int,
    unit: str,
    interpretation: str,
    inputs: BaseModel,
    components: list[Component] | None = None,
) -> CalculatorResult:
    spec = get_calculator(calculator_id)
    value, value_display = format_rounded(precise, digits)
    return CalculatorResult(
        calculator_id=calculator_id,
        name=spec.name,
        value=value,
        value_display=value_display,
        unit=unit,
        interpretation=interpretation,
        formula=spec.formula,
        reference=spec.reference,
        inputs_used=inputs.model_dump(mode="json"),
        components=components or [],
    )
