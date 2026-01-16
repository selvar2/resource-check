@echo off
:: ============================================================
:: Battery Health Guardian - Debug Launcher (with console)
:: Shows logs and error messages for troubleshooting
:: ============================================================

cd /d "%~dp0"

echo ============================================================
echo  Battery Health Guardian - Debug Mode
echo ============================================================
echo.

:: Check if embedded Python exists
if exist "python-embedded\python.exe" (
    echo Using embedded Python...
    set PYTHONPATH=%~dp0vendor;%~dp0
    python-embedded\python.exe run_guardian.py
) else (
    :: Fallback to system Python with vendored dependencies
    if exist "vendor\psutil" (
        echo Using system Python with vendored dependencies...
        set PYTHONPATH=%~dp0vendor;%~dp0
        python run_guardian.py
    ) else (
        :: Fallback to system Python
        echo Using system Python...
        python run_guardian.py
    )
)

echo.
echo Application closed. Press any key to exit...
pause > nul
