from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from mcp_calc.methodology import METHODOLOGY


class InputOption(BaseModel):
    value: str
    label: str


class InputSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    label: str
    type: Literal["number", "integer", "boolean", "enum"]
    unit: str | None = None
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None
    default: Any = None
    options: list[InputOption] | None = None
    help: str | None = None


class CalculatorSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    summary: str
    formula: str
    reference: str
    methodology: str
    inputs: list[InputSpec]


_SEX = [
    InputOption(value="male", label="Мужской"),
    InputOption(value="female", label="Женский"),
]
_CREATININE_UNIT = [
    InputOption(value="umol_l", label="мкмоль/л"),
    InputOption(value="mg_dl", label="мг/дл"),
]


def _sex(default: str = "male") -> InputSpec:
    return InputSpec(
        name="sex",
        label="Пол",
        type="enum",
        default=default,
        options=_SEX,
    )


def _creatinine(default: float = 88) -> InputSpec:
    return InputSpec(
        name="creatinine",
        label="Креатинин",
        type="number",
        minimum=0.1,
        maximum=4000,
        step=0.1,
        default=default,
        help="Введите число в выбранных единицах. 88 мкмоль/л ≈ 1,0 мг/дл.",
    )


def _creatinine_unit() -> InputSpec:
    return InputSpec(
        name="creatinine_unit",
        label="Единица креатинина",
        type="enum",
        default="umol_l",
        options=_CREATININE_UNIT,
    )


def _age(minimum: int = 18, default: int = 50, help_text: str | None = None) -> InputSpec:
    return InputSpec(
        name="age_years",
        label="Возраст",
        type="integer",
        unit="лет",
        minimum=minimum,
        maximum=120,
        step=1,
        default=default,
        help=help_text,
    )


def _weight(default: float = 70) -> InputSpec:
    return InputSpec(
        name="weight_kg",
        label="Масса",
        type="number",
        unit="кг",
        minimum=0.5,
        maximum=400,
        step=0.1,
        default=default,
    )


def _height(default: float = 175) -> InputSpec:
    return InputSpec(
        name="height_cm",
        label="Рост",
        type="number",
        unit="см",
        minimum=40,
        maximum=250,
        step=0.5,
        default=default,
    )


CALCULATORS: tuple[CalculatorSpec, ...] = (
    CalculatorSpec(
        id="bmi",
        name="Индекс массы тела",
        summary="Индекс массы тела по массе и росту. Категории — пороги WHO.",
        formula="BMI = масса_кг / рост_м²",
        reference="WHO. Obesity: preventing and managing the global epidemic. WHO Technical Report Series 894, 2000.",
        methodology=METHODOLOGY["bmi"],
        inputs=[_weight(), _height()],
    ),
    CalculatorSpec(
        id="bsa_mosteller",
        name="Площадь поверхности тела",
        summary="Площадь поверхности тела по формуле Mosteller.",
        formula="BSA = √(рост_см × масса_кг / 3600)",
        reference="Mosteller RD. Simplified calculation of body-surface area. N Engl J Med. 1987;317:1098.",
        methodology=METHODOLOGY["bsa_mosteller"],
        inputs=[_weight(), _height()],
    ),
    CalculatorSpec(
        id="egfr_ckd_epi_2021",
        name="рСКФ CKD-EPI 2021",
        summary="Расчётная скорость клубочковой фильтрации по креатинину, уравнение CKD-EPI 2021 без расового коэффициента.",
        formula="142 × min(Scr/κ, 1)^α × max(Scr/κ, 1)^(−1.200) × 0.9938^возраст × 1.012 для женщин",
        reference="Inker LA, et al. N Engl J Med. 2021;385:1737-1749. Категории СКФ: KDIGO 2012.",
        methodology=METHODOLOGY["egfr_ckd_epi_2021"],
        inputs=[
            _age(help_text="Уравнение CKD-EPI 2021 предназначено для взрослых от 18 лет."),
            _sex(),
            _creatinine(),
            _creatinine_unit(),
        ],
    ),
    CalculatorSpec(
        id="cockcroft_gault",
        name="Клиренс креатинина",
        summary="Оценка клиренса креатинина по Cockcroft–Gault. Результат не нормирован на 1,73 м².",
        formula="((140 − возраст) × масса_кг × 0,85 для женщин) / (72 × Scr_мг/дл). Масса — введённое значение.",
        reference="Cockcroft DW, Gault MH. Prediction of creatinine clearance from serum creatinine. Nephron. 1976;16:31-41.",
        methodology=METHODOLOGY["cockcroft_gault"],
        inputs=[
            _age(help_text="Формула описана для взрослых."),
            _sex(),
            _weight(),
            _creatinine(),
            _creatinine_unit(),
        ],
    ),
    CalculatorSpec(
        id="cha2ds2_vasc",
        name="CHA₂DS₂-VASc",
        summary="Сумма баллов шкалы риска инсульта при фибрилляции предсердий.",
        formula="ХСН + гипертензия + возраст≥75 (2) + диабет + инсульт/ТИА (2) + сосудистое заболевание + возраст 65–74 + женский пол",
        reference="Lip GY, et al. Chest. 2010;137:263-272. Пороги категорий — учебная справка по шкале, не назначение лечения.",
        methodology=METHODOLOGY["cha2ds2_vasc"],
        inputs=[
            _age(default=72),
            _sex(),
            InputSpec(
                name="congestive_heart_failure",
                label="Хроническая сердечная недостаточность",
                type="boolean",
                default=False,
                help="Сердечная недостаточность или дисфункция левого желудочка.",
            ),
            InputSpec(
                name="hypertension",
                label="Артериальная гипертензия",
                type="boolean",
                default=False,
            ),
            InputSpec(
                name="diabetes",
                label="Сахарный диабет",
                type="boolean",
                default=False,
            ),
            InputSpec(
                name="stroke_tia_thromboembolism",
                label="Инсульт, ТИА или тромбоэмболия",
                type="boolean",
                default=False,
            ),
            InputSpec(
                name="vascular_disease",
                label="Сосудистое заболевание",
                type="boolean",
                default=False,
                help="Перенесённый инфаркт миокарда, периферический атеросклероз или атеросклероз аорты.",
            ),
        ],
    ),
    CalculatorSpec(
        id="curb65",
        name="CURB-65",
        summary="Шкала тяжести внебольничной пневмонии.",
        formula="Нарушение сознания + мочевина > 7 ммоль/л + ЧДД ≥ 30 + низкое АД + возраст ≥ 65",
        reference="Lim WS, et al. Defining community acquired pneumonia severity on presentation to hospital. Thorax. 2003;58:377-382.",
        methodology=METHODOLOGY["curb65"],
        inputs=[
            _age(default=70),
            InputSpec(
                name="confusion",
                label="Новое нарушение сознания",
                type="boolean",
                default=False,
            ),
            InputSpec(
                name="urea_mmol_l",
                label="Мочевина",
                type="number",
                unit="ммоль/л",
                minimum=0,
                maximum=80,
                step=0.1,
                default=6.5,
                help="Мочевина плазмы. Порог балла — строго больше 7 ммоль/л, это не BUN в мг/дл.",
            ),
            InputSpec(
                name="respiratory_rate",
                label="Частота дыхания",
                type="integer",
                unit="в минуту",
                minimum=4,
                maximum=80,
                step=1,
                default=20,
            ),
            InputSpec(
                name="systolic_bp",
                label="Систолическое АД",
                type="integer",
                unit="мм рт. ст.",
                minimum=40,
                maximum=300,
                step=1,
                default=120,
            ),
            InputSpec(
                name="diastolic_bp",
                label="Диастолическое АД",
                type="integer",
                unit="мм рт. ст.",
                minimum=20,
                maximum=200,
                step=1,
                default=80,
            ),
        ],
    ),
    CalculatorSpec(
        id="qtc",
        name="Корригированный QT",
        summary="QTc по формулам Bazett и Fridericia из измеренного QT и частоты пульса.",
        formula="Bazett: QT / √RR. Fridericia: QT / RR^(1/3). RR в секундах, QT в миллисекундах.",
        reference="Bazett HC. Heart. 1920;7:353-370. Fridericia LS. Acta Med Scand. 1920;53:469-486. Пороги удлинения: Rautaharju PM, et al. Circulation. 2009;119:e241.",
        methodology=METHODOLOGY["qtc"],
        inputs=[
            InputSpec(
                name="qt_ms",
                label="Интервал QT",
                type="integer",
                unit="мс",
                minimum=200,
                maximum=800,
                step=1,
                default=400,
                help="Измеренный QT, не уже корригированный QTc.",
            ),
            InputSpec(
                name="heart_rate_bpm",
                label="Частота сердечных сокращений",
                type="integer",
                unit="уд/мин",
                minimum=30,
                maximum=250,
                step=1,
                default=60,
            ),
            _sex(),
        ],
    ),
)


class CalculatorCatalog(BaseModel):
    calculators: list[CalculatorSpec]


def get_calculator(calculator_id: str) -> CalculatorSpec:
    for spec in CALCULATORS:
        if spec.id == calculator_id:
            return spec
    raise KeyError(calculator_id)
