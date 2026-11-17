# Скачивает исходные шрифты (Allo 1.0 и Inter 4.1) и раскладывает в vendor/.
# Нужны только те файлы, которые реально использует сборка.
$ErrorActionPreference = "Stop"

$root = Split-Path $PSScriptRoot -Parent
$vendor = Join-Path $root "vendor"
$tmp = Join-Path $env:TEMP "allo-cyr-src"

$alloUrl = "https://github.com/joshpuckett/allo/releases/download/v1.0/Allo-1.0.zip"
$interUrl = "https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip"

New-Item -ItemType Directory -Force -Path $tmp, $vendor | Out-Null

if (-not (Test-Path (Join-Path $tmp "Allo-1.0.zip"))) {
    Write-Host "downloading Allo-1.0.zip"
    curl.exe -sL -o (Join-Path $tmp "Allo-1.0.zip") $alloUrl
}
if (-not (Test-Path (Join-Path $tmp "Inter-4.1.zip"))) {
    Write-Host "downloading Inter-4.1.zip (34 MB)"
    curl.exe -sL -o (Join-Path $tmp "Inter-4.1.zip") $interUrl
}

$allo = Join-Path $tmp "allo"
$inter = Join-Path $tmp "inter"
if (-not (Test-Path (Join-Path $allo "Allo-1.0"))) {
    Expand-Archive -Path (Join-Path $tmp "Allo-1.0.zip") -DestinationPath $allo -Force
}
if (-not (Test-Path (Join-Path $inter "extras"))) {
    Expand-Archive -Path (Join-Path $tmp "Inter-4.1.zip") -DestinationPath $inter -Force
}

New-Item -ItemType Directory -Force -Path `
    (Join-Path $vendor "allo\fonts\variable"), `
    (Join-Path $vendor "allo\fonts\otf"), `
    (Join-Path $vendor "allo\fonts\webfonts"), `
    (Join-Path $vendor "inter") | Out-Null

Copy-Item (Join-Path $allo "Allo-1.0\fonts\variable\AlloVariable.ttf") (Join-Path $vendor "allo\fonts\variable\") -Force
Copy-Item (Join-Path $allo "Allo-1.0\fonts\otf\Allo-Regular.otf") (Join-Path $vendor "allo\fonts\otf\") -Force
Copy-Item (Join-Path $allo "Allo-1.0\fonts\webfonts\Allo-Regular.woff2") (Join-Path $vendor "allo\fonts\webfonts\") -Force
Copy-Item (Join-Path $allo "Allo-1.0\OFL.txt") (Join-Path $vendor "allo\OFL.txt") -Force
Copy-Item (Join-Path $inter "LICENSE.txt") (Join-Path $vendor "inter\LICENSE.txt") -Force

foreach ($w in @("Regular", "Medium", "Bold")) {
    Copy-Item (Join-Path $inter "extras\ttf\Inter-$w.ttf") (Join-Path $vendor "inter\") -Force
}

Write-Host "vendor/ ready:"
Get-ChildItem $vendor -Recurse -File | ForEach-Object {
    "  " + $_.FullName.Substring($vendor.Length + 1) + "  " + [math]::Round($_.Length / 1KB) + " KB"
}
