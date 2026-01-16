@echo off
:: ============================================================
:: Battery Health Guardian - Build Script
:: Creates standalone executable using PyInstaller
:: ============================================================

cd /d "%~dp0"

echo ============================================================
echo  Battery Health Guardian - Build Process
echo ============================================================
echo.

:: Check for Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.8+ or use embedded Python
    pause
    exit /b 1
)

:: Check for PyInstaller
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

:: Create releases directory
if not exist "releases" mkdir releases

echo.
echo Building standalone executable...
echo.

:: Build with PyInstaller
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name BatteryHealthGuardian ^
    --add-data "battery_guardian\config.json;battery_guardian" ^
    --hidden-import pystray._win32 ^
    --hidden-import PIL._tkinter_finder ^
    --hidden-import winotify ^
    --distpath releases ^
    --workpath build\pyinstaller ^
    --specpath build ^
    --clean ^
    run_guardian.pyw

if %errorlevel%==0 (
    echo.
    echo ============================================================
    echo  Build Successful!
    echo ============================================================
    echo.
    echo Executable: releases\BatteryHealthGuardian.exe
    echo.
    
    :: Generate checksum
    echo Generating checksum...
    certutil -hashfile releases\BatteryHealthGuardian.exe SHA256 > releases\checksums.txt 2>&1
    echo Checksum saved to: releases\checksums.txt
) else (
    echo.
    echo ============================================================
    echo  Build Failed!
    echo ============================================================
    echo Check the error messages above.
)

echo.
pause
