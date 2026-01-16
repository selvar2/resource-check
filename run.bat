@echo off
:: ============================================================
:: Battery Health Guardian - One-Click Launcher
:: No installation required - uses embedded Python + vendored deps
:: ============================================================

cd /d "%~dp0"

:: Check if embedded Python exists
if exist "python-embedded\python.exe" (
    echo Starting Battery Health Guardian with embedded Python...
    set PYTHONPATH=%~dp0vendor;%~dp0
    python-embedded\pythonw.exe run_guardian.pyw
) else (
    :: Fallback to system Python with vendored dependencies
    if exist "vendor\psutil" (
        echo Starting Battery Health Guardian with vendored dependencies...
        set PYTHONPATH=%~dp0vendor;%~dp0
        pythonw run_guardian.pyw
    ) else (
        :: Fallback to system Python
        echo Starting Battery Health Guardian with system Python...
        pythonw run_guardian.pyw
    )
)
