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
  --exclude=data/*.db `
  --exclude=__pycache__ `
  --exclude=*.pyc `
  -C $Root .

Write-Host "=== 3. Upload ===" -ForegroundColor Cyan
scp $Archive "${Remote}:/tmp/chislyandia-deploy.tgz"

if (Test-Path "$Root\.env") {
    Write-Host "=== 3b. Upload .env ===" -ForegroundColor Cyan
    scp "$Root\.env" "${Remote}:${RemoteDir}/.env"
}

Write-Host "=== 4. Remote setup ===" -ForegroundColor Cyan
$RemoteScript = @'
set -e
mkdir -p /opt/chislyandia
tar -xzf /tmp/chislyandia-deploy.tgz -C /opt/chislyandia
chown -R juliabot:juliabot /opt/chislyandia
mkdir -p /opt/chislyandia/data /opt/chislyandia/logs
chown -R juliabot:juliabot /opt/chislyandia/data /opt/chislyandia/logs

if [ ! -d /opt/chislyandia/venv ]; then
  python3 -m venv /opt/chislyandia/venv
fi
/opt/chislyandia/venv/bin/pip install -q -U pip
/opt/chislyandia/venv/bin/pip install -q -r /opt/chislyandia/requirements-web.txt

cd /opt/chislyandia
/opt/chislyandia/venv/bin/python -c "from database.schema import init_database; init_database('data/progress.db')"

apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq nginx

cp /opt/chislyandia/deploy/chislyandia-api.service /etc/systemd/system/chislyandia-api.service
cp /opt/chislyandia/deploy/nginx-chislyandia.conf /etc/nginx/sites-available/chislyandia
ln -sf /etc/nginx/sites-available/chislyandia /etc/nginx/sites-enabled/chislyandia
rm -f /etc/nginx/sites-enabled/default

systemctl daemon-reload
systemctl enable chislyandia-api nginx
systemctl restart chislyandia-api nginx

sleep 2
curl -sf http://127.0.0.1:5000/api/health || true
curl -sf http://127.0.0.1/api/health || true
echo "DEPLOY_OK"
'@

ssh $Remote $RemoteScript

Write-Host ""
Write-Host "=== Staging ready ===" -ForegroundColor Green
Write-Host "$StagingUrl/api/health"
Write-Host "$StagingUrl/game/menu/331113480"
