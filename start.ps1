$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $PSScriptRoot ".browsers"
$env:PYTHONPATH = $PSScriptRoot
if (-not $env:INTERMARKET_REAL_CHROME) {
    # Use local Chrome when Patchright Chromium is missing (optional).
    if (Test-Path "C:\Program Files\Google\Chrome\Application\chrome.exe") {
        $env:INTERMARKET_REAL_CHROME = "1"
    }
}

Write-Host "Updating data and starting dashboard at http://127.0.0.1:8765/ ..."
python main.py start @args
