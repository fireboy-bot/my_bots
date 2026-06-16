# Деплой Chislyandia на Timeweb staging (147.45.225.173)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Remote = "timeweb-vps"
$RemoteDir = "/opt/chislyandia"
$StagingUrl = "http://147.45.225.173"

Write-Host "=== 1. Build frontend (staging) ===" -ForegroundColor Cyan
Copy-Item "$Root\frontend\.env.staging" "$Root\frontend\.env.production.local" -Force
Set-Location "$Root\frontend"
npm run build
Set-Location $Root

Write-Host "=== 2. Pack archive ===" -ForegroundColor Cyan
$Archive = Join-Path $env:TEMP "chislyandia-deploy.tgz"
if (Test-Path $Archive) { Remove-Item $Archive -Force }

tar -czf $Archive `
  --exclude=venv `
  --exclude=node_modules `
  --exclude=frontend/node_modules `
  --exclude=.git `
  --exclude=logs `
  --exclude=data/progress.db `
  --exclude=data/progress.db-shm `
  --exclude=data/progress.db-wal `
  --exclude=data/*.db `
  --exclude=__pycache__ `
  --exclude=*.pyc `
  -C $Root .

Write-Host "=== 3. Upload ===" -ForegroundColor Cyan
ssh $Remote "mkdir -p $RemoteDir"
scp $Archive "${Remote}:/tmp/chislyandia-deploy.tgz"
scp "$Root\deploy\remote-setup.sh" "${Remote}:/tmp/chislyandia-setup.sh"

if (Test-Path "$Root\.env") {
    Write-Host "=== 3b. Upload .env ===" -ForegroundColor Cyan
    scp "$Root\.env" "${Remote}:${RemoteDir}/.env"
}

Write-Host "=== 4. Remote setup ===" -ForegroundColor Cyan
ssh $Remote "sed -i 's/\r$//' /tmp/chislyandia-setup.sh; bash /tmp/chislyandia-setup.sh"

Write-Host ""
Write-Host "=== Staging ready ===" -ForegroundColor Green
Write-Host "$StagingUrl/api/health"
Write-Host "$StagingUrl/game/menu/331113480"
