import pytest
from mcp_calc.external_client import (
    get_external_server_parameters,
    fetch_external_tools_sync,
    call_external_tool_sync,
)


def test_get_external_server_parameters():
    params = get_external_server_parameters()
    assert params is not None
    assert params.command
    assert "PUPPETEER_SKIP_DOWNLOAD" in params.env


def test_fetch_external_tools_and_call():
    tools = fetch_external_tools_sync()
    assert len(tools) >= 5
    names = {t["name"] for t in tools}
    assert "search-drugs" in names
    assert "search-medical-literature" in names

    # Call search-drugs with acetaminophen
    result = call_external_tool_sync("search-drugs", {"query": "acetaminophen", "limit": 1})
    assert isinstance(result, str)
    assert len(result) > 0
    assert "acetaminophen" in result.lower()
