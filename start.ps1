<#
    One-command local start for the AI Customer Support Platform (Windows / PowerShell).

    What it does:
      1. Creates a .venv virtual environment if one does not exist
      2. Installs the project (and dev tools) into it
      3. Creates .env from .env.example if you don't have one yet
      4. Starts the server at http://localhost:8000

    Usage:
      .\start.ps1              # start on port 8000
      .\start.ps1 -Port 8080   # start on a different port

    If PowerShell blocks the script, run it once as:
      powershell -ExecutionPolicy Bypass -File .\start.ps1
#>
param(
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$python = "python"
try { & $python --version | Out-Null } catch {
    Write-Error "Python was not found on PATH. Install Python 3.11+ from https://www.python.org/downloads/ and re-run."
    exit 1
}

if (-not (Test-Path ".venv")) {
    Write-Host "==> Creating virtual environment (.venv)..." -ForegroundColor Cyan
    & $python -m venv .venv
}

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

Write-Host "==> Installing dependencies..." -ForegroundColor Cyan
& $venvPython -m pip install --upgrade pip --quiet
& $venvPython -m pip install -e ".[dev]" --quiet

if (-not (Test-Path ".env")) {
    Write-Host "==> Creating .env from .env.example (edit it to add ANTHROPIC_API_KEY)..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}

$env:PORT = "$Port"
Write-Host ""
Write-Host "==> Starting AI Customer Support Platform" -ForegroundColor Green
Write-Host "    Web UI    ->  http://localhost:$Port/"
Write-Host "    API docs  ->  http://localhost:$Port/docs"
Write-Host ""
& $venvPython -m app
