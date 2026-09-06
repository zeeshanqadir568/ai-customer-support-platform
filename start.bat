@echo off
REM One-command local start for the AI Customer Support Platform (Windows / cmd.exe).
REM   1. creates .venv if missing   2. installs deps   3. makes .env   4. runs the server
REM Usage:  start.bat            (port 8000)
REM         set PORT=8080 ^& start.bat

setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found on PATH. Install Python 3.11+ from https://www.python.org/downloads/ and re-run.
    exit /b 1
)

if not exist ".venv" (
    echo ==^> Creating virtual environment ^(.venv^)...
    python -m venv .venv
)

set "VENV_PY=.venv\Scripts\python.exe"

echo ==^> Installing dependencies...
"%VENV_PY%" -m pip install --upgrade pip --quiet
"%VENV_PY%" -m pip install -e ".[dev]" --quiet

if not exist ".env" (
    echo ==^> Creating .env from .env.example ^(edit it to add ANTHROPIC_API_KEY^)...
    copy /y ".env.example" ".env" >nul
)

if "%PORT%"=="" set "PORT=8000"
echo.
echo ==^> Starting AI Customer Support Platform
echo     Web UI    -^>  http://localhost:%PORT%/
echo     API docs  -^>  http://localhost:%PORT%/docs
echo.
"%VENV_PY%" -m app
