# Полный перезапуск Web (API + подсказка для фронта)
# Запуск: powershell -ExecutionPolicy Bypass -File scripts\restart-web.ps1

$ErrorActionPreference = "SilentlyContinue"
$root = Split-Path -Parent $PSScriptRoot

Write-Host "=== Chislyandia: остановка старых процессов ===" -ForegroundColor Cyan

foreach ($port in @(5000, 5173)) {
    Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
        ForEach-Object {
            Write-Host "  Порт $port -> PID $($_.OwningProcess)" -ForegroundColor Yellow
            Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
        }
}

Start-Sleep -Seconds 1

Write-Host "`n=== Запуск API (ядро) на http://127.0.0.1:5000 ===" -ForegroundColor Green
$env:PYTHONIOENCODING = "utf-8"
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$root'; .\venv\Scripts\python.exe web\api_server.py"
)

Write-Host "`n=== Фронт (в НОВОМ окне терминала) ===" -ForegroundColor Green
Write-Host "cd $root\frontend"
Write-Host "npm run dev"
Write-Host "`nОткрой: http://localhost:5173/game/menu/ТВОЙ_USER_ID"
Write-Host "Проверка API: http://127.0.0.1:5000/api/health"
Write-Host "`nCtrl+Shift+R в браузере (жёсткое обновление)!" -ForegroundColor Magenta
