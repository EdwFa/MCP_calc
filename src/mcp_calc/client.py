"""Короткоживущий MCP-клиент по stdio. Каждая операция поднимает сервер и закрывает его."""

import asyncio
import json
import sys
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


def _server_parameters() -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_calc.server"],
        env={"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
    )


def _text(result: Any) -> str:
    parts: list[str] = []
    for block in getattr(result, "content", None) or []:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts).strip()


def payload_from_result(result: Any) -> Any:
    if getattr(result, "is_error", False):
        message = _text(result) or "MCP tool вернул ошибку без текста."
        raise RuntimeError(message)
    structured = getattr(result, "structured_content", None)
    if structured is not None:
        return structured
    text = _text(result)
    if not text:
        raise RuntimeError("MCP tool вернул пустой ответ.")
    return json.loads(text)


def _unwrap_group(exc: BaseException) -> BaseException:
    current = exc
    while isinstance(current, BaseExceptionGroup) and len(current.exceptions) == 1:
        current = current.exceptions[0]
    return current


async def _with_session(callback):
    try:
        async with stdio_client(_server_parameters()) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await callback(session)
    except BaseExceptionGroup as exc:
        unwrapped = _unwrap_group(exc)
        if unwrapped is exc:
            raise
        raise unwrapped from exc


async def call_tool(name: str, arguments: dict[str, Any] | None = None) -> Any:
    async def _run(session: ClientSession):
        result = await session.call_tool(name, arguments or {})
        return payload_from_result(result)

    return await _with_session(_run)


async def fetch_demo_state() -> dict[str, Any]:
    async def _run(session: ClientSession):
        listed = await session.list_tools()
        catalog = payload_from_result(await session.call_tool("list_calculators", {}))
        return {
            "tool_names": [tool.name for tool in listed.tools],
            "calculators": catalog["calculators"],
        }

    return await _with_session(_run)


def run_async(coro):
    return asyncio.run(coro)


def call_tool_sync(name: str, arguments: dict[str, Any] | None = None) -> Any:
    return run_async(call_tool(name, arguments))


def fetch_demo_state_sync() -> dict[str, Any]:
    return run_async(fetch_demo_state())
