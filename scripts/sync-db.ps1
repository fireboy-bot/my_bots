# Синхронизация progress.db и отдельных пользователей: local <-> staging VPS
# Совместимо с Windows PowerShell 5.1 (без оператора &&)
param(
    [Parameter(Position = 0)]
    [ValidateSet("pull-db", "push-db", "pull-user", "push-user", "configure-demo")]
    [string]$Action = "pull-user",
    [string]$UserId = "331113480"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Remote = "timeweb-vps"
$RemoteDir = "/opt/chislyandia"
$LocalDb = Join-Path $Root "data\progress.db"
$ExportDir = Join-Path $Root "data\sync"
$DemoUser = "331113480"

function Ensure-ExportDir {
    if (-not (Test-Path $ExportDir)) {
        New-Item -ItemType Directory -Path $ExportDir | Out-Null
    }
}

function Invoke-Remote {
    param([string]$Command)
    ssh $Remote $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Remote command failed (exit $LASTEXITCODE): $Command"
    }
}

switch ($Action) {
    "pull-db" {
        $backup = Join-Path $Root "data\progress.from-vps.db"
        Write-Host "=== Download VPS DB -> $backup ===" -ForegroundColor Cyan
        scp "${Remote}:${RemoteDir}/data/progress.db" $backup
        if ($LASTEXITCODE -ne 0) { throw "scp failed" }
        Write-Host "OK. Local app still uses data\progress.db — swap manually if needed." -ForegroundColor Green
    }
    "push-db" {
        if (-not (Test-Path $LocalDb)) {
            throw "Local DB not found: $LocalDb"
        }
        Write-Host "=== Backup VPS DB and upload local progress.db ===" -ForegroundColor Yellow
        $ts = Get-Date -Format "yyyyMMdd-HHmmss"
        Invoke-Remote "cp ${RemoteDir}/data/progress.db ${RemoteDir}/data/progress.backup-${ts}.db"
        scp $LocalDb "${Remote}:${RemoteDir}/data/progress.db"
        if ($LASTEXITCODE -ne 0) { throw "scp failed" }
        Invoke-Remote "systemctl restart chislyandia-api"
        Write-Host "OK. VPS DB replaced, API restarted." -ForegroundColor Green
    }
    "pull-user" {
        Ensure-ExportDir
        $remoteJson = "/tmp/chislyandia_user_${UserId}.json"
        $localJson = Join-Path $ExportDir "user_${UserId}.from-vps.json"
        Write-Host "=== Pull user $UserId from VPS ===" -ForegroundColor Cyan
        Invoke-Remote "cd $RemoteDir; ./venv/bin/python scripts/sync_user_db.py export $UserId --db data/progress.db -o $remoteJson"
        scp "${Remote}:${remoteJson}" $localJson
        if ($LASTEXITCODE -ne 0) { throw "scp failed" }
        & "$Root\venv\Scripts\python.exe" "$Root\scripts\sync_user_db.py" import $UserId --db data/progress.db -i $localJson
        if ($LASTEXITCODE -ne 0) { throw "local import failed" }
        Write-Host "OK. User imported to local data\progress.db" -ForegroundColor Green
    }
    "push-user" {
        Ensure-ExportDir
        $localJson = Join-Path $ExportDir "user_${UserId}.to-vps.json"
        $remoteJson = "/tmp/chislyandia_user_${UserId}.json"
        Write-Host "=== Push user $UserId to VPS ===" -ForegroundColor Cyan
        & "$Root\venv\Scripts\python.exe" "$Root\scripts\sync_user_db.py" export $UserId --db data/progress.db -o $localJson
        if ($LASTEXITCODE -ne 0) { throw "local export failed" }
        scp $localJson "${Remote}:${remoteJson}"
        if ($LASTEXITCODE -ne 0) { throw "scp failed" }
        Invoke-Remote "cd $RemoteDir; ./venv/bin/python scripts/sync_user_db.py import $UserId --db data/progress.db -i $remoteJson"
        Invoke-Remote "systemctl restart chislyandia-api"
        Write-Host "OK. User synced on VPS, API restarted." -ForegroundColor Green
    }
    "configure-demo" {
        Write-Host "=== Configure demo user on VPS ($DemoUser) ===" -ForegroundColor Cyan
        Invoke-Remote "cd $RemoteDir; ./venv/bin/python scripts/configure-demo-user.py"
        Invoke-Remote "systemctl restart chislyandia-api"
        Write-Host "OK. Demo user ready for True Lord test." -ForegroundColor Green
    }
}
