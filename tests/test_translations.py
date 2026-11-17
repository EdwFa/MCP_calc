from mcp_calc.translations import (
    translate_tool_name,
    translate_tool_purpose,
    translate_specialty,
    translate_param_name,
    translate_severity,
    translate_unit,
    translate_component_label,
    translate_recommendations,
    translate_summary,
)


def test_translations():
    # Tools
    assert "CKD-EPI 2021" in translate_tool_name("ckd_epi_2021", "CKD-EPI")
    assert "CURB-65" in translate_tool_name("curb65", "CURB-65")

    # Specialties
    assert translate_specialty("cardiology") == "Кардиология"
    assert translate_specialty("nephrology") == "Нефрология"

    # Params
    assert translate_param_name("age") == "Возраст пациента"
    assert translate_param_name("serum_creatinine") == "Креатинин сыворотки крови"

    # Units
    assert translate_unit("points") == "баллов"
    assert translate_unit("mL/min/1.73m²") == "мл/мин/1,73 м²"

    # Severity
    assert "Высокий" in translate_severity("high")
    assert "Низкий" in translate_severity("low")

    # Component labels
    assert "Нарушение сознания" in translate_component_label("Confusion")

    # Recommendations
    sepsis_rec = (
        "Per Sepsis-3: SOFA ≥2 indicates organ dysfunction in suspected infection; "
        "Follow Surviving Sepsis Campaign Hour-1 Bundle if sepsis suspected; "
        "Reassess SOFA every 24 hours to monitor trajectory; "
        "Consider early goal-directed therapy and source control; "
        "Obtain blood cultures if not already done; "
        "Administer broad-spectrum antibiotics within 1 hour if sepsis; "
        "Begin fluid resuscitation (30 mL/kg crystalloid); "
        "Measure serum lactate; "
        "Initiate vasopressors if hypotensive after fluid resuscitation"
    )
    translated_recs = translate_recommendations(sepsis_rec)
    assert len(translated_recs) == 9
    assert any(("sepsis" in r.lower() or "сепсис" in r.lower()) and "органн" in r for r in translated_recs)
    assert any("Surviving Sepsis" in r or "сепсис" in r.lower() for r in translated_recs)
    assert any("антибиотик" in r.lower() for r in translated_recs)
    assert any("лактат" in r.lower() for r in translated_recs)
    assert any("вазопрессор" in r.lower() for r in translated_recs)

    # Summary
    sum_text = "CURB-65 = 3: High risk (14.5% 30-day mortality)"
    translated_sum = translate_summary(sum_text)
    assert "Высокий риск" in translated_sum
    assert "30-дневн" in translated_sum
