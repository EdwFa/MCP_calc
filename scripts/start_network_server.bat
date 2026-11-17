@echo off
echo Starting medical-calc-mcp SSE server on http://127.0.0.1:8000 ...
cd /d "%~dp0\..\servers\medical-calc-mcp"
".venv\Scripts\python.exe" -m src.main --mode sse --host 127.0.0.1 --port 8000
