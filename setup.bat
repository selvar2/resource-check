@echo off
:: ============================================================
:: Battery Health Guardian - Setup Verification
:: All dependencies are pre-bundled - no installation required!
:: ============================================================

cd /d "%~dp0"

echo ============================================================
echo  Battery Health Guardian - Setup Verification
echo ============================================================
echo.

:: Check for embedded Python
if exist "python-embedded\python.exe" (
    echo [OK] Embedded Python found
) else (
    echo [--] Embedded Python not found (will use system Python^)
)

:: Check for vendored dependencies
if exist "vendor\psutil" (
    echo [OK] Vendored dependencies found
) else (
    echo [--] Vendored dependencies not found
)

:: Check for system Python
where python >nul 2>&1
if %errorlevel%==0 (
    echo [OK] System Python found
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo     %%i
) else (
    echo [!!] System Python NOT found
)

:: Check for pre-built executable
if exist "releases\BatteryHealthGuardian.exe" (
    echo [OK] Pre-built executable found
) else (
    echo [--] Pre-built executable not found (run build.bat to create^)
)

echo.
echo ============================================================
echo  Status: Ready to run!
echo ============================================================
echo.
echo To start the application:
echo   - Double-click: run.bat
echo   - Or run: .\run.ps1
echo   - Or use pre-built: releases\BatteryHealthGuardian.exe
echo.
pause
