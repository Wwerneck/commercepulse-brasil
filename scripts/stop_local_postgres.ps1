$ErrorActionPreference = "Stop"

$pgBin = "C:\Program Files\PostgreSQL\16\bin"
$dataDir = Join-Path (Get-Location) ".local\postgres\data"

if (Test-Path $dataDir) {
    & "$pgBin\pg_ctl.exe" -D $dataDir stop
}
