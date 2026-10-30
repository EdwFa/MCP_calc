from typing import Any

from pydantic import ValidationError

from mcp_calc.calculators import COMPUTE, INPUT_MODELS
from mcp_calc.registry import CALCULATORS, get_calculator


def calculator_catalog() -> dict[str, Any]:
    return {
        "calculators": [spec.model_dump(mode="json", exclude_none=True) for spec in CALCULATORS],
    }


def format_validation_error(calculator_id: str, exc: ValidationError) -> str:
    labels = {item.name: item.label for item in get_calculator(calculator_id).inputs}
    parts: list[str] = []
    for error in exc.errors():
        field = str(error["loc"][0]) if error["loc"] else "поле"
        label = labels.get(field, field)
        parts.append(f"{label}: {error['msg']}")
    return "Некорректные входные данные — " + "; ".join(parts)


def run_calculator(calculator_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        model = INPUT_MODELS[calculator_id]
        compute = COMPUTE[calculator_id]
    except KeyError as exc:
        known = ", ".join(INPUT_MODELS)
        raise ValueError(f"Неизвестный калькулятор «{calculator_id}». Доступны: {known}.") from exc
    try:
        parsed = model.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(format_validation_error(calculator_id, exc)) from exc
    return compute(parsed).model_dump(mode="json")
