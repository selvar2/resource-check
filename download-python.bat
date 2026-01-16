@echo off
:: ============================================================
:: Battery Health Guardian - Download Embedded Python
:: Downloads portable Python for zero-install deployment
:: ============================================================

cd /d "%~dp0"

echo ============================================================
echo  Downloading Embedded Python
echo ============================================================
echo.

:: Python version to download
set PYTHON_VERSION=3.12.1
set PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-embed-amd64.zip
set DOWNLOAD_FILE=python-embedded.zip

:: Check if already exists
if exist "python-embedded\python.exe" (
    echo Embedded Python already exists.
    set /p overwrite="Overwrite? (y/n): "
    if /i not "%overwrite%"=="y" (
        echo Skipped.
        goto :install_pip
    )
    rmdir /s /q python-embedded 2>nul
)

echo Downloading Python %PYTHON_VERSION% embedded...
echo URL: %PYTHON_URL%
echo.

:: Download using PowerShell
powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%DOWNLOAD_FILE%'"

if not exist "%DOWNLOAD_FILE%" (
    echo ERROR: Download failed!
    pause
    exit /b 1
)

echo Extracting...
if not exist "python-embedded" mkdir python-embedded
powershell -Command "Expand-Archive -Path '%DOWNLOAD_FILE%' -DestinationPath 'python-embedded' -Force"

:: Clean up
del "%DOWNLOAD_FILE%" 2>nul

:install_pip
echo.
echo Installing pip in embedded Python...

:: Enable pip in embedded Python by modifying python*._pth file
for %%f in (python-embedded\python*._pth) do (
    echo import site >> "%%f"
)

:: Download get-pip.py
powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'python-embedded\get-pip.py'"

:: Install pip
python-embedded\python.exe python-embedded\get-pip.py --no-warn-script-location

:: Install dependencies
echo.
echo Installing dependencies...
python-embedded\python.exe -m pip install psutil pystray Pillow winotify --no-warn-script-location

echo.
echo ============================================================
echo  Embedded Python Setup Complete!
echo ============================================================
echo.
echo Location: python-embedded\
echo Python: python-embedded\python.exe
echo.
pause
