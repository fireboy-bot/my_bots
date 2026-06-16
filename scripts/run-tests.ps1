# Smoke-тесты API (День 4)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Python = Join-Path $Root "venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Error "venv не найден. Создай venv в корне проекта."
}

$env:PYTHONIOENCODING = "utf-8"
& $Python -m pytest tests/ -v --tb=short
