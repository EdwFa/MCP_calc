"""Тесты поискового механизма клинических калькуляторов в GUI."""

import json
import os
import pytest
from mcp_calc.translations import (
    NETWORK_TOOLS_RU,
    get_tool_keywords,
    translate_tool_name,
    translate_tool_purpose,
)


def _build_search_corpus(tool_id: str, tool_data: dict) -> str:
    ru_name = translate_tool_name(tool_id, tool_data.get("name", tool_id))
    ru_purpose = translate_tool_purpose(tool_id, tool_data.get("purpose", ""))
    keywords = get_tool_keywords(tool_id)
    specialties = tool_data.get("specialties", [])

    return " ".join([
        tool_id,
        tool_data.get("name", ""),
        ru_name,
        tool_data.get("purpose", ""),
        ru_purpose,
        " ".join(keywords),
        " ".join(specialties),
    ]).lower()


def test_inf_search_finds_all_infarction_and_infection_tools():
    """Проверка, что поиск по 'инф' находит и инфаркты, и инфекции, и инфузии."""
    assert len(NETWORK_TOOLS_RU) == 152

    matches = []
    for tid, meta in NETWORK_TOOLS_RU.items():
        corpus = _build_search_corpus(tid, meta)
        if "инф" in corpus:
            matches.append(tid)

    # Должно быть найдено свыше 20 калькуляторов
    assert len(matches) >= 20

    # Инфаркты
    assert "timi_stemi" in matches
    assert "grace_score" in matches
    assert "heart_score" in matches
    assert "rcri" in matches
    assert "score2" in matches
    assert "framingham_risk_score" in matches
    assert "euroscore_ii" in matches
    assert "acef_ii" in matches

    # Инфекции
    assert "cpis" in matches
    assert "curb65" in matches
    assert "psi_port" in matches
    assert "sofa_score" in matches
    assert "sofa2_score" in matches
    assert "qsofa_score" in matches
    assert "sirs_criteria" in matches

    # Инфузии
    assert "transfusion_calc" in matches
    assert "free_water_deficit" in matches
    assert "parkland_formula" in matches
    assert "pediatric_dosing" in matches


def test_infarct_specific_search():
    """Проверка, что поиск по слову 'инфаркт' находит все кардиологические калькуляторы инфаркта."""
    matches = []
    for tid, meta in NETWORK_TOOLS_RU.items():
        corpus = _build_search_corpus(tid, meta)
        if "инфаркт" in corpus:
            matches.append(tid)

    assert len(matches) >= 7
    assert "timi_stemi" in matches
    assert "grace_score" in matches
    assert "heart_score" in matches
    assert "rcri" in matches


def test_infection_specific_search():
    """Проверка, что поиск по слову 'инфекция' находит все инфекционные шкалы."""
    matches = []
    for tid, meta in NETWORK_TOOLS_RU.items():
        corpus = _build_search_corpus(tid, meta)
        if "инфекция" in corpus:
            matches.append(tid)

    assert len(matches) >= 8
    assert "cpis" in matches
    assert "curb65" in matches
    assert "sofa_score" in matches
    assert "qsofa_score" in matches
    assert "sirs_criteria" in matches
