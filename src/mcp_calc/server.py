"""MCP-сервер учебных медицинских калькуляторов. Транспорт по умолчанию — stdio."""

from typing import Annotated

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp_types import ToolAnnotations
from pydantic import Field

from mcp_calc.domain import CreatinineUnit, Sex
from mcp_calc.models import CalculatorResult
from mcp_calc.registry import CalculatorCatalog, get_calculator
from mcp_calc.service import calculator_catalog, run_calculator

_READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)

mcp = MCPServer(
    "medical-calculators",
    instructions=(
        "Учебные медицинские калькуляторы. Каждый tool считает одну опубликованную формулу "
        "и возвращает число, пояснение порогов и дисклеймер. Результат не является диагнозом "
        "или назначением лечения. Список полей и подписи — в tool list_calculators."
    ),
    log_level="WARNING",
)


def _result(calculator_id: str, payload: dict) -> CalculatorResult:
    try:
        raw = run_calculator(calculator_id, payload)
    except ValueError as exc:
        raise ToolError(str(exc)) from exc
    return CalculatorResult.model_validate(raw)


def _register(calculator_id: str):
    spec = get_calculator(calculator_id)
    return mcp.tool(title=spec.name, description=spec.summary, annotations=_READ_ONLY)


@mcp.tool(
    title="Список калькуляторов",
    description="Названия, формулы, источники и поля ввода всех калькуляторов.",
    annotations=_READ_ONLY,
)
def list_calculators() -> CalculatorCatalog:
    """Каталог калькуляторов для построения формы."""
    return CalculatorCatalog.model_validate(calculator_catalog())


@_register("bmi")
def bmi(
    weight_kg: Annotated[float, Field(description="Масса тела, кг")],
    height_cm: Annotated[float, Field(description="Рост, см")],
) -> CalculatorResult:
    return _result("bmi", {"weight_kg": weight_kg, "height_cm": height_cm})


@_register("bsa_mosteller")
def bsa_mosteller(
    weight_kg: Annotated[float, Field(description="Масса тела, кг")],
    height_cm: Annotated[float, Field(description="Рост, см")],
) -> CalculatorResult:
    return _result("bsa_mosteller", {"weight_kg": weight_kg, "height_cm": height_cm})


@_register("egfr_ckd_epi_2021")
def egfr_ckd_epi_2021(
    age_years: Annotated[int, Field(description="Возраст, полных лет, от 18")],
    sex: Annotated[Sex, Field(description="Пол: male или female")],
    creatinine: Annotated[float, Field(description="Креатинин сыворотки")],
    creatinine_unit: Annotated[CreatinineUnit, Field(description="Единица креатинина: umol_l или mg_dl")],
) -> CalculatorResult:
    return _result(
        "egfr_ckd_epi_2021",
        {
            "age_years": age_years,
            "sex": sex,
            "creatinine": creatinine,
            "creatinine_unit": creatinine_unit,
        },
    )


@_register("cockcroft_gault")
def cockcroft_gault(
    age_years: Annotated[int, Field(description="Возраст, полных лет, от 18")],
    sex: Annotated[Sex, Field(description="Пол: male или female")],
    weight_kg: Annotated[float, Field(description="Масса тела, кг. В формулу идёт это значение")],
    creatinine: Annotated[float, Field(description="Креатинин сыворотки")],
    creatinine_unit: Annotated[CreatinineUnit, Field(description="Единица креатинина: umol_l или mg_dl")],
) -> CalculatorResult:
    return _result(
        "cockcroft_gault",
        {
            "age_years": age_years,
            "sex": sex,
            "weight_kg": weight_kg,
            "creatinine": creatinine,
            "creatinine_unit": creatinine_unit,
        },
    )


@_register("cha2ds2_vasc")
def cha2ds2_vasc(
    age_years: Annotated[int, Field(description="Возраст, полных лет")],
    sex: Annotated[Sex, Field(description="Пол: male или female")],
    congestive_heart_failure: Annotated[bool, Field(description="Сердечная недостаточность или дисфункция ЛЖ")],
    hypertension: Annotated[bool, Field(description="Артериальная гипертензия")],
    diabetes: Annotated[bool, Field(description="Сахарный диабет")],
    stroke_tia_thromboembolism: Annotated[bool, Field(description="Инсульт, ТИА или артериальная тромбоэмболия")],
    vascular_disease: Annotated[
        bool,
        Field(description="Инфаркт миокарда, периферический атеросклероз или атеросклероз аорты"),
    ],
) -> CalculatorResult:
    return _result(
        "cha2ds2_vasc",
        {
            "age_years": age_years,
            "sex": sex,
            "congestive_heart_failure": congestive_heart_failure,
            "hypertension": hypertension,
            "diabetes": diabetes,
            "stroke_tia_thromboembolism": stroke_tia_thromboembolism,
            "vascular_disease": vascular_disease,
        },
    )


@_register("curb65")
def curb65(
    age_years: Annotated[int, Field(description="Возраст, полных лет")],
    confusion: Annotated[bool, Field(description="Новое нарушение сознания")],
    urea_mmol_l: Annotated[float, Field(description="Мочевина плазмы, ммоль/л. Балл даёт значение строго больше 7")],
    respiratory_rate: Annotated[int, Field(description="Частота дыхания в минуту")],
    systolic_bp: Annotated[int, Field(description="Систолическое АД, мм рт. ст.")],
    diastolic_bp: Annotated[int, Field(description="Диастолическое АД, мм рт. ст.")],
) -> CalculatorResult:
    return _result(
        "curb65",
        {
            "age_years": age_years,
            "confusion": confusion,
            "urea_mmol_l": urea_mmol_l,
            "respiratory_rate": respiratory_rate,
            "systolic_bp": systolic_bp,
            "diastolic_bp": diastolic_bp,
        },
    )


@_register("qtc")
def qtc(
    qt_ms: Annotated[int, Field(description="Измеренный интервал QT, мс, не QTc")],
    heart_rate_bpm: Annotated[int, Field(description="Частота сердечных сокращений, ударов в минуту")],
    sex: Annotated[Sex, Field(description="Пол: male или female. Нужен для порога удлинения")],
) -> CalculatorResult:
    return _result("qtc", {"qt_ms": qt_ms, "heart_rate_bpm": heart_rate_bpm, "sex": sex})


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
