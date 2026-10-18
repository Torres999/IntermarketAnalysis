$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $PSScriptRoot ".browsers"
$env:PYTHONPATH = $PSScriptRoot
python main.py scrape
Write-Host "Done. Start dashboard: python main.py serve"
