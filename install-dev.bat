@echo off
:: ============================================================
:: Battery Health Guardian - Developer Setup
:: Installs fresh dependencies to vendor folder
:: Only needed if you want to rebuild the vendor folder
:: ============================================================

cd /d "%~dp0"

echo ============================================================
echo  Battery Health Guardian - Developer Setup
echo ============================================================
echo.
echo This will install dependencies to the vendor folder.
echo NOTE: Dependencies are already bundled - only run this if
echo       you need to update or rebuild the vendor folder.
echo.

set /p confirm="Continue? (y/n): "
if /i not "%confirm%"=="y" (
    echo Cancelled.
    pause
    exit /b 0
)

:: Check for Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found in PATH
    pause
    exit /b 1
)

:: Create vendor directory
if not exist "vendor" mkdir vendor

echo.
echo Installing dependencies to vendor folder...
echo.

:: Install dependencies to vendor folder
pip install ^
    psutil ^
    pystray ^
    Pillow ^
    winotify ^
    --target vendor ^
    --upgrade

if %errorlevel%==0 (
    echo.
    echo ============================================================
    echo  Installation Complete!
    echo ============================================================
    echo Dependencies installed to: vendor\
) else (
    echo.
    echo Installation failed. Check error messages above.
)

echo.
pause
