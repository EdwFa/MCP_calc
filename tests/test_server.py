import asyncio

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from mcp_calc.registry import CALCULATORS


def test_server_registers_every_calculator():
    from mcp_calc.server import mcp

    tools = asyncio.run(mcp.list_tools())
    names = {tool.name for tool in tools}
    assert names == {spec.id for spec in CALCULATORS} | {"list_calculators"}


def test_inprocess_tool_returns_bmi_and_validation_error():
    from mcp_calc.server import mcp

    result = asyncio.run(mcp.call_tool("bmi", {"weight_kg": 70, "height_cm": 175}))
    assert result.structured_content["value_display"] == "22.9"
    assert result.is_error is not True

    with pytest.raises(ToolError, match="Возраст"):
        asyncio.run(
            mcp.call_tool(
                "egfr_ckd_epi_2021",
                {"age_years": 10, "sex": "male", "creatinine": 80, "creatinine_unit": "umol_l"},
            )
        )


def test_stdio_client_lists_tools_and_calculates_bmi():
    from mcp_calc.client import call_tool_sync, fetch_demo_state_sync

    state = fetch_demo_state_sync()
    assert "bmi" in state["tool_names"]
    assert "list_calculators" in state["tool_names"]
    assert {item["id"] for item in state["calculators"]} == {spec.id for spec in CALCULATORS}

    result = call_tool_sync("bsa_mosteller", {"weight_kg": 70, "height_cm": 175})
    assert result["value_display"] == "1.84"

    with pytest.raises(RuntimeError, match="Возраст"):
        call_tool_sync(
            "egfr_ckd_epi_2021",
            {"age_years": 10, "sex": "male", "creatinine": 80, "creatinine_unit": "umol_l"},
        )
