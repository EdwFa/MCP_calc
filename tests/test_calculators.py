import pytest

from mcp_calc.calculators.bmi import bmi_category
from mcp_calc.calculators.cha2ds2_vasc import cha2ds2_band
from mcp_calc.calculators.cockcroft_gault import clearance_band
from mcp_calc.calculators.curb65 import curb65_severity
from mcp_calc.calculators.egfr import gfr_category
from mcp_calc.calculators.qtc import qtc_band
from mcp_calc.domain import Sex
from mcp_calc.formatting import plural_points, round_half_up
from mcp_calc.registry import CALCULATORS
from mcp_calc.service import run_calculator


def _components(result: dict) -> dict[str, str]:
    return {item["label"]: item["value"] for item in result["components"]}


def test_round_half_up_is_not_bankers_rounding():
    assert round_half_up(2.5, 0) == 3
    assert round_half_up(1.25, 1) == 1.3
    assert round_half_up(22.857142857142858, 1) == 22.9


def test_plural_points():
    assert plural_points(1) == "балл"
    assert plural_points(2) == "балла"
    assert plural_points(5) == "баллов"
    assert plural_points(11) == "баллов"


def test_bmi_known_value_and_category():
    result = run_calculator("bmi", {"weight_kg": 70, "height_cm": 175})
    assert result["value_display"] == "22.9"
    assert result["unit"] == "кг/м²"
    assert result["interpretation"] == "Категория WHO: нормальная масса тела."
    assert "консультацию врача" in result["disclaimer"]


@pytest.mark.parametrize(
    ("bmi", "expected"),
    [
        (18.4, "недостаточная масса тела"),
        (18.5, "нормальная масса тела"),
        (24.9, "нормальная масса тела"),
        (25, "избыточная масса тела"),
        (30, "ожирение I степени"),
        (35, "ожирение II степени"),
        (40, "ожирение III степени"),
    ],
)
def test_bmi_who_boundaries(bmi, expected):
    assert bmi_category(bmi) == expected


def test_bsa_mosteller_known_value():
    result = run_calculator("bsa_mosteller", {"weight_kg": 70, "height_cm": 175})
    assert result["value_display"] == "1.84"
    assert result["unit"] == "м²"


def test_egfr_male_default_creatinine_and_female_published_inputs():
    male = run_calculator(
        "egfr_ckd_epi_2021",
        {"age_years": 50, "sex": "male", "creatinine": 88, "creatinine_unit": "umol_l"},
    )
    assert male["value_display"] == "92.2"
    assert "G1" in male["interpretation"]

    female = run_calculator(
        "egfr_ckd_epi_2021",
        {"age_years": 65, "sex": "female", "creatinine": 1.0, "creatinine_unit": "mg_dl"},
    )
    assert female["value_display"] == "62.5"
    assert "G2" in female["interpretation"]


def test_egfr_very_high_creatinine_is_g5():
    result = run_calculator(
        "egfr_ckd_epi_2021",
        {"age_years": 70, "sex": "male", "creatinine": 8, "creatinine_unit": "mg_dl"},
    )
    assert result["value_display"] == "6.7"
    assert "G5" in result["interpretation"]


@pytest.mark.parametrize(
    ("gfr", "code"),
    [
        (90, "G1"),
        (89.9, "G2"),
        (60, "G2"),
        (59.9, "G3a"),
        (45, "G3a"),
        (44.9, "G3b"),
        (30, "G3b"),
        (29.9, "G4"),
        (15, "G4"),
        (14.9, "G5"),
    ],
)
def test_kdigo_boundaries(gfr, code):
    assert gfr_category(gfr)[0] == code


def test_cockcroft_gault_exact_cases():
    male = run_calculator(
        "cockcroft_gault",
        {
            "age_years": 50,
            "sex": "male",
            "weight_kg": 70,
            "creatinine": 1,
            "creatinine_unit": "mg_dl",
        },
    )
    assert male["value_display"] == "87.5"
    assert clearance_band(87.5) == "60–89 мл/мин"

    female = run_calculator(
        "cockcroft_gault",
        {
            "age_years": 50,
            "sex": "female",
            "weight_kg": 70,
            "creatinine": 1,
            "creatinine_unit": "mg_dl",
        },
    )
    assert female["value_display"] == "74.4"
    assert _components(female)["Коэффициент пола"] == "0.85"


def test_cha2ds2_vasc_points_are_mutually_exclusive_for_age():
    result = run_calculator(
        "cha2ds2_vasc",
        {
            "age_years": 76,
            "sex": "female",
            "congestive_heart_failure": True,
            "hypertension": True,
            "diabetes": False,
            "stroke_tia_thromboembolism": True,
            "vascular_disease": False,
        },
    )
    assert result["value_display"] == "7"
    assert result["unit"] == "баллов"
    points = _components(result)
    assert points["Возраст ≥75 лет"] == "2"
    assert points["Возраст 65–74 года"] == "0"
    assert points["Женский пол"] == "1"
    assert "высокая категория для женщины" in result["interpretation"]


@pytest.mark.parametrize(
    ("score", "sex", "fragment"),
    [
        (0, Sex.male, "низкая категория для мужчины"),
        (1, Sex.male, "промежуточная категория для мужчины"),
        (2, Sex.male, "высокая категория для мужчины"),
        (1, Sex.female, "низкая категория для женщины"),
        (2, Sex.female, "промежуточная категория для женщины"),
        (3, Sex.female, "высокая категория для женщины"),
    ],
)
def test_cha2ds2_bands(score, sex, fragment):
    assert fragment in cha2ds2_band(score, sex)


def test_curb65_scores_thresholds_and_rejects_inverted_bp():
    low = run_calculator(
        "curb65",
        {
            "age_years": 64,
            "confusion": False,
            "urea_mmol_l": 7,
            "respiratory_rate": 20,
            "systolic_bp": 120,
            "diastolic_bp": 61,
        },
    )
    assert low["value_display"] == "0"
    assert curb65_severity(0) == "низкая тяжесть"

    urea_point = run_calculator(
        "curb65",
        {
            "age_years": 64,
            "confusion": False,
            "urea_mmol_l": 7.1,
            "respiratory_rate": 29,
            "systolic_bp": 90,
            "diastolic_bp": 61,
        },
    )
    assert _components(urea_point)["Мочевина > 7 ммоль/л"] == "1"
    assert _components(urea_point)["Частота дыхания ≥ 30"] == "0"
    assert _components(urea_point)["САД < 90 или ДАД ≤ 60"] == "0"

    high = run_calculator(
        "curb65",
        {
            "age_years": 70,
            "confusion": True,
            "urea_mmol_l": 8,
            "respiratory_rate": 32,
            "systolic_bp": 85,
            "diastolic_bp": 60,
        },
    )
    assert high["value_display"] == "5"
    assert "высокая тяжесть" in high["interpretation"]

    with pytest.raises(ValueError, match="Диастолическое давление"):
        run_calculator(
            "curb65",
            {
                "age_years": 70,
                "confusion": False,
                "urea_mmol_l": 5,
                "respiratory_rate": 18,
                "systolic_bp": 80,
                "diastolic_bp": 90,
            },
        )


def test_qtc_resting_rate_and_formula_disagreement():
    resting = run_calculator("qtc", {"qt_ms": 400, "heart_rate_bpm": 60, "sex": "male"})
    assert resting["value_display"] == "400"
    assert _components(resting)["QTc Bazett"].startswith("400 мс")
    assert _components(resting)["QTc Fridericia"].startswith("400 мс")

    fast = run_calculator("qtc", {"qt_ms": 400, "heart_rate_bpm": 80, "sex": "male"})
    assert fast["value_display"] == "462"
    assert _components(fast)["QTc Fridericia"].startswith("440 мс")
    assert "разные категории" in fast["interpretation"]


@pytest.mark.parametrize(
    ("qtc", "sex", "expected"),
    [
        (449, Sex.male, "в пределах этих порогов"),
        (450, Sex.male, "удлинённый"),
        (459, Sex.female, "в пределах этих порогов"),
        (460, Sex.female, "удлинённый"),
        (500, Sex.female, "выраженно удлинённый"),
        (350, Sex.male, "укороченный"),
    ],
)
def test_qtc_bands(qtc, sex, expected):
    assert qtc_band(qtc, sex) == expected


def test_defaults_from_the_catalog_are_valid():
    for spec in CALCULATORS:
        payload = {item.name: item.default for item in spec.inputs}
        result = run_calculator(spec.id, payload)
        assert result["calculator_id"] == spec.id
        assert result["formula"] == spec.formula
        assert result["name"] == spec.name


def test_registry_fields_match_input_models():
    from mcp_calc.calculators import INPUT_MODELS

    assert [spec.id for spec in CALCULATORS] == list(INPUT_MODELS)
    for spec in CALCULATORS:
        model_fields = list(INPUT_MODELS[spec.id].model_fields)
        assert [item.name for item in spec.inputs] == model_fields


def test_each_calculator_publishes_methodology_markdown():
    from mcp_calc.methodology import METHODOLOGY

    assert set(METHODOLOGY) == {spec.id for spec in CALCULATORS}
    for spec in CALCULATORS:
        assert spec.methodology == METHODOLOGY[spec.id]
        assert spec.methodology.startswith("## ")
        assert "$$" in spec.methodology or "| --- |" in spec.methodology


def test_invalid_input_is_a_russian_validation_error():
    with pytest.raises(ValueError, match="Возраст"):
        run_calculator(
            "egfr_ckd_epi_2021",
            {"age_years": 10, "sex": "male", "creatinine": 80, "creatinine_unit": "umol_l"},
        )
    with pytest.raises(ValueError, match="единицу измерения"):
        run_calculator(
            "egfr_ckd_epi_2021",
            {"age_years": 50, "sex": "male", "creatinine": 80, "creatinine_unit": "mg_dl"},
        )


def test_unknown_calculator():
    with pytest.raises(ValueError, match="Неизвестный калькулятор"):
        run_calculator("apgar", {})
