$ErrorActionPreference = "Stop"

$pgBin = "C:\Program Files\PostgreSQL\16\bin"
$dataDir = Join-Path (Get-Location) ".local\postgres\data"
$logDir = Join-Path (Get-Location) ".local\postgres"
$logFile = Join-Path $logDir "postgres.log"
$port = "55432"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

if (-not (Test-Path $dataDir)) {
    & "$pgBin\initdb.exe" -D $dataDir -U commercepulse --auth=trust --encoding=UTF8
}

& "$pgBin\pg_ctl.exe" -D $dataDir -l $logFile -o "-p $port" start
Start-Sleep -Seconds 2

& "$pgBin\createdb.exe" -h localhost -p $port -U commercepulse commercepulse
if ($LASTEXITCODE -ne 0) {
    Write-Host "Database may already exist; continuing."
}

Write-Host "Local project PostgreSQL is running on localhost:$port"
