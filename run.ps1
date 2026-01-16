# ============================================================
# Battery Health Guardian - PowerShell Launcher
# No installation required - uses embedded Python + vendored deps
# ============================================================

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Set PYTHONPATH to include vendor folder
$env:PYTHONPATH = "$scriptDir\vendor;$scriptDir"

if (Test-Path "$scriptDir\python-embedded\python.exe") {
    Write-Host "Starting Battery Health Guardian with embedded Python..." -ForegroundColor Green
    Start-Process -FilePath "$scriptDir\python-embedded\pythonw.exe" -ArgumentList "run_guardian.pyw" -NoNewWindow
}
elseif (Test-Path "$scriptDir\vendor\psutil") {
    Write-Host "Starting Battery Health Guardian with vendored dependencies..." -ForegroundColor Green
    Start-Process -FilePath "pythonw" -ArgumentList "run_guardian.pyw" -NoNewWindow
}
else {
    Write-Host "Starting Battery Health Guardian with system Python..." -ForegroundColor Yellow
    Start-Process -FilePath "pythonw" -ArgumentList "run_guardian.pyw" -NoNewWindow
}

Write-Host "Application started! Check system tray for the battery icon." -ForegroundColor Cyan
