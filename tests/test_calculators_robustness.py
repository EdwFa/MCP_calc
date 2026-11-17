"""Тесты устойчивости калькуляторов к типам параметров."""

import pytest
from mcp_calc.network_client import calculate_network_sync


def test_child_pugh_string_and_numeric_robustness():
    """Child-Pugh должен успешно рассчитываться как со строками, так и с числами."""
    res = calculate_network_sync("child_pugh", {
        "bilirubin": 1.0,
        "albumin": 3.5,
        "inr": 1.0,
        "ascites": "none",
        "encephalopathy_grade": 0,
    })
    assert res.get("success") is True
    assert res.get("result") == 6


def test_euroscore_ii_calculation():
    """EuroSCORE II должен успешно рассчитываться с категориальными параметрами."""
    res = calculate_network_sync("euroscore_ii", {
        "age": 65,
        "gender": "male",
        "creatinine_clearance": 75.0,
        "extracardiac_arteriopathy": 0,
        "poor_mobility": 0,
        "previous_cardiac_surgery": 0,
        "chronic_lung_disease": 0,
        "active_endocarditis": 0,
        "critical_preop_state": 0,
        "diabetes_on_insulin": 0,
        "nyha_class": 2,
        "ccs_class_4_angina": 0,
        "lvef": "good",
        "recent_mi": 0,
        "pulmonary_hypertension": "none",
        "urgency": "elective",
        "weight_of_intervention": "isolated_cabg",
        "surgery_on_thoracic_aorta": 0,
    })
    assert res.get("success") is True
    assert res.get("result") is not None


def test_transfusion_calc():
    """Transfusion volume calculation."""
    res = calculate_network_sync("transfusion_calc", {
        "weight_kg": 70.0,
        "current_hematocrit": 21.0,
        "target_hematocrit": 30.0,
        "product_type": "prbc",
        "patient_type": "adult",
    })
    assert res.get("success") is True
    assert res.get("result") > 0


def test_pediatric_dosing():
    """Pediatric drug dosing calculation."""
    res = calculate_network_sync("pediatric_dosing", {
        "weight_kg": 20.0,
        "age_years": 5.0,
        "drug_name": "acetaminophen",
    })
    assert res.get("success") is True
    assert res.get("result") > 0


def test_bishop_score():
    """Bishop score calculation."""
    res = calculate_network_sync("bishop_score", {
        "dilation": 2,
        "effacement": 2,
        "station": 1,
        "consistency": "medium",
        "position": "mid",
    })
    assert res.get("success") is True
    assert res.get("result") == 7.0


def test_triss():
    """TRISS survival probability calculation."""
    res = calculate_network_sync("triss", {
        "iss": 15,
        "age": 45,
        "injury_type": "blunt",
        "gcs": 15,
        "systolic_bp": 120,
        "respiratory_rate": 16,
    })
    assert res.get("success") is True
    assert res.get("result") > 90.0
