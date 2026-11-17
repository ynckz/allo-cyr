# Полная сборка: TTF -> woff2 -> dist/AlloCyr-1.0.zip
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path "vendor\allo\fonts\variable\AlloVariable.ttf")) {
    Write-Host "vendor/ is empty - fetching sources first"
    & "$PSScriptRoot\build\fetch-sources.ps1"
}

Write-Host "`n== TTF, со скруглением =="
python build/merge.py

Write-Host "`n== TTF, без скругления (для сравнения) =="
python build/merge.py --no-round --out=out/ttf/plain

Write-Host "`n== woff2 =="
python build/subset.py

Write-Host "`n== dist/AlloCyr-1.0.zip =="
if (Test-Path "dist\AlloCyr-1.0.zip") { Remove-Item "dist\AlloCyr-1.0.zip" -Force }
Compress-Archive -Path `
    "out\ttf\AlloCyr-Regular.ttf", `
    "out\ttf\AlloCyr-Medium.ttf", `
    "out\ttf\AlloCyr-Bold.ttf", `
    "OFL.txt", `
    "dist\README.txt" `
    -DestinationPath "dist\AlloCyr-1.0.zip" -Force
"  dist/AlloCyr-1.0.zip  " + [math]::Round((Get-Item "dist\AlloCyr-1.0.zip").Length / 1KB) + " KB"
