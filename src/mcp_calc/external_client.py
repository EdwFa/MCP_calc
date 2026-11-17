"""Клиент для внешнего MCP-сервера medical-mcp (FDA, PubMed, WHO, RxNorm)."""

import asyncio
import os
import shutil
import sys
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


def get_external_server_parameters() -> StdioServerParameters:
    """Определяет способ запуска medical-mcp на текущей системе."""
    env = os.environ.copy()
    env["PUPPETEER_SKIP_DOWNLOAD"] = "true"

    # 1. Проверяем глобальный путь npm
    appdata = os.environ.get("APPDATA", "")
    global_index = os.path.join(appdata, "npm", "node_modules", "medical-mcp", "build", "index.js")
    if os.path.exists(global_index):
        node_bin = shutil.which("node") or "node"
        return StdioServerParameters(
            command=node_bin,
            args=[global_index],
            env=env,
        )

    # 2. Проверяем команду medical-mcp в PATH
    medical_cmd = shutil.which("medical-mcp") or shutil.which("medical-mcp.cmd")
    if medical_cmd:
        if sys.platform == "win32" and medical_cmd.endswith((".cmd", ".bat")):
            return StdioServerParameters(
                command="cmd.exe",
                args=["/c", medical_cmd],
                env=env,
            )
        return StdioServerParameters(
            command=medical_cmd,
            args=[],
            env=env,
        )

    # 3. Fallback через npx
    if sys.platform == "win32":
        return StdioServerParameters(
            command="cmd.exe",
            args=["/c", "npx", "-y", "medical-mcp"],
            env=env,
        )
    return StdioServerParameters(
        command="npx",
        args=["-y", "medical-mcp"],
        env=env,
    )


def _unwrap_group(exc: BaseException) -> BaseException:
    current = exc
    while isinstance(current, BaseExceptionGroup) and len(current.exceptions) == 1:
        current = current.exceptions[0]
    return current


async def _with_external_session(callback):
    params = get_external_server_parameters()
    try:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await callback(session)
    except BaseExceptionGroup as exc:
        unwrapped = _unwrap_group(exc)
        if unwrapped is exc:
            raise
        raise unwrapped from exc


async def fetch_external_tools() -> list[dict[str, Any]]:
    """Получает список доступных инструментов внешнего medical-mcp сервера."""
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

    return await _with_external_session(_run)


async def call_external_tool(name: str, arguments: dict[str, Any] | None = None) -> str:
    """Вызывает инструмент внешнего MCP-сервера."""
    async def _run(session: ClientSession):
        result = await session.call_tool(name, arguments or {})
        if getattr(result, "is_error", False):
            parts = []
            for block in getattr(result, "content", None) or []:
                text = getattr(block, "text", None)
                if text:
                    parts.append(text)
            err_msg = "\n".join(parts).strip() or "Внешний MCP tool вернул ошибку."
            raise RuntimeError(err_msg)

        # Собираем текстовое содержимое
        parts = []
        for block in getattr(result, "content", None) or []:
            text = getattr(block, "text", None)
            if text:
                parts.append(text)
        return "\n".join(parts).strip()

    return await _with_external_session(_run)


def fetch_external_tools_sync() -> list[dict[str, Any]]:
    return asyncio.run(fetch_external_tools())


def call_external_tool_sync(name: str, arguments: dict[str, Any] | None = None) -> str:
    return asyncio.run(call_external_tool(name, arguments))
