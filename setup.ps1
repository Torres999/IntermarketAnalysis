$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $PSScriptRoot ".browsers"
if (-not $env:PLAYWRIGHT_DOWNLOAD_HOST) {
    $env:PLAYWRIGHT_DOWNLOAD_HOST = "https://registry.npmmirror.com/-/binary/playwright"
}

python -m pip install -r requirements.txt

Write-Host "Installing Chromium for Scrapling (Patchright) into .browsers ..."
Write-Host "If download fails, set INTERMARKET_REAL_CHROME=1 when Google Chrome is installed."
Remove-Item -Recurse -Force (Join-Path $env:PLAYWRIGHT_BROWSERS_PATH "__dirlock") -ErrorAction SilentlyContinue
patchright install chromium

Write-Host "Setup complete. Run: python main.py run"
