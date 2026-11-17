import pytest
from mcp_calc.network_client import (
    DEFAULT_SSE_URL,
    fetch_network_tools_sync,
    discover_calculators_sync,
    get_calculator_schema_sync,
    calculate_network_sync,
)


def test_fetch_network_tools():
    tools = fetch_network_tools_sync()
    names = {t["name"] for t in tools}
    assert "discover" in names
    assert "calculate" in names
    assert "get_tool_schema" in names


def test_discover_and_calculate_ckd():
    # Discover calculators
    discovered = discover_calculators_sync(by="tools")
    assert discovered.get("success") is True
    tools_list = discovered.get("tools", [])
    assert len(tools_list) > 0

    # Get schema for ckd_epi_2021
    schema = get_calculator_schema_sync("ckd_epi_2021")
    assert schema.get("success") is True
    assert schema.get("tool_id") == "ckd_epi_2021"

    # Calculate
    calc_res = calculate_network_sync(
        "ckd_epi_2021",
        {"creatinine": 1.0, "age": 50, "gender": "male"}
    )
    assert calc_res.get("success") is True
    assert calc_res.get("result") is not None
    assert "mL/min" in calc_res.get("unit", "")
