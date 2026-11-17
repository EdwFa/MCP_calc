"""Клиент для сетевого MCP-сервера medical-calc-mcp (152 клинических калькулятора по SSE)."""

import asyncio
import os
import sys
from typing import Any

from mcp import ClientSession
from mcp.client.sse import sse_client

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

DEFAULT_SSE_URL = os.environ.get("MEDICAL_CALC_SSE_URL", "http://127.0.0.1:8000/sse")


def _unwrap_group(exc: BaseException) -> BaseException:
    current = exc
    while isinstance(current, BaseExceptionGroup) and len(current.exceptions) == 1:
        current = current.exceptions[0]
    return current


async def _with_sse_session(callback, sse_url: str = DEFAULT_SSE_URL):
    try:
        async with sse_client(sse_url) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await callback(session)
    except BaseExceptionGroup as exc:
        unwrapped = _unwrap_group(exc)
        if unwrapped is exc:
            raise
        raise unwrapped from exc


async def fetch_network_tools(sse_url: str = DEFAULT_SSE_URL) -> list[dict[str, Any]]:
    """Получает список мета-инструментов сетевого MCP-сервера."""
    async def _run(session: ClientSession):
        listed = await session.list_tools()
        tools = []
        for t in listed.tools:
            tools.append({
                "name": t.name,
                "description": t.description or "",
                "input_schema": t.input_schema or {},
            })
        return tools

    return await _with_sse_session(_run, sse_url)


async def discover_calculators(by: str = "tools", value: str = "", limit: int = 250, sse_url: str = DEFAULT_SSE_URL) -> dict[str, Any]:
    """Вызывает инструмент discover для поиска калькуляторов."""
    import json

    async def _run(session: ClientSession):
        args: dict[str, Any] = {"by": by, "limit": limit}
        if value:
            args["value"] = value
        result = await session.call_tool("discover", args)
        for block in getattr(result, "content", None) or []:
            text = getattr(block, "text", None)
            if text:
                try:
                    return json.loads(text)
                except Exception:
                    return {"raw": text}
        return {}

    return await _with_sse_session(_run, sse_url)


async def get_calculator_schema(tool_id: str, sse_url: str = DEFAULT_SSE_URL) -> dict[str, Any]:
    """Получает схему параметров и метаданные конкретного калькулятора."""
    import json

    async def _run(session: ClientSession):
        result = await session.call_tool("get_tool_schema", {"tool_id": tool_id})
        for block in getattr(result, "content", None) or []:
            text = getattr(block, "text", None)
            if text:
                try:
                    return json.loads(text)
                except Exception:
                    return {"raw": text}
        return {}

    return await _with_sse_session(_run, sse_url)


STRING_PARAM_DEFAULTS: dict[str, str] = {
    "gender": "male",
    "sex": "male",
    "ascites": "none",
    "lvef": "good",
    "urgency": "elective",
    "weight_of_intervention": "isolated_cabg",
    "pulmonary_hypertension": "none",
    "product_type": "prbc",
    "patient_type": "adult",
    "consistency": "medium",
    "position": "mid",
    "injury_type": "blunt",
    "risk_region": "low",
    "formula": "mosteller",
    "drug_name": "acetaminophen",
    "opioid_name": "morphine_oral",
    "secretions": "none_light",
    "chest_xray": "no_infiltrate",
    "culture_growth": "none_light",
    "age_group": "adult",
    "vasopressor_type": "none",
    "pupillary_reaction": "both_react",
    "burden_of_illness": "none_mild",
    "consciousness": "alert",
    "temperature_category": "normal",
    "mental_status": "alert",
}


def sanitize_network_calc_params(params: dict[str, Any]) -> dict[str, Any]:
    """Предотвращает ошибки типов, заменяя числовой 0.0 на корректные строковые enum-значения."""
    cleaned = dict(params)
    for k, v in list(cleaned.items()):
        if k in STRING_PARAM_DEFAULTS and isinstance(v, (int, float)):
            if v == 0 or v == 0.0:
                cleaned[k] = STRING_PARAM_DEFAULTS[k]
            else:
                cleaned[k] = str(int(v)) if isinstance(v, int) or v == int(v) else str(v)
    return cleaned


async def calculate_network(tool_id: str, params: dict[str, Any], sse_url: str = DEFAULT_SSE_URL) -> dict[str, Any]:
    """Выполняет медицинский расчёт через сетевой MCP-сервер."""
    import json

    sanitized_params = sanitize_network_calc_params(params)

    async def _run(session: ClientSession):
        result = await session.call_tool("calculate", {"tool_id": tool_id, "params": sanitized_params})
        for block in getattr(result, "content", None) or []:
            text = getattr(block, "text", None)
            if text:
                try:
                    return json.loads(text)
                except Exception:
                    return {"raw": text}
        return {}

    return await _with_sse_session(_run, sse_url)


def fetch_network_tools_sync(sse_url: str = DEFAULT_SSE_URL) -> list[dict[str, Any]]:
    return asyncio.run(fetch_network_tools(sse_url))


def discover_calculators_sync(by: str = "tools", value: str = "", limit: int = 250, sse_url: str = DEFAULT_SSE_URL) -> dict[str, Any]:
    return asyncio.run(discover_calculators(by, value, limit, sse_url))


def get_calculator_schema_sync(tool_id: str, sse_url: str = DEFAULT_SSE_URL) -> dict[str, Any]:
    return asyncio.run(get_calculator_schema(tool_id, sse_url))


def calculate_network_sync(tool_id: str, params: dict[str, Any], sse_url: str = DEFAULT_SSE_URL) -> dict[str, Any]:
    return asyncio.run(calculate_network(tool_id, params, sse_url))
