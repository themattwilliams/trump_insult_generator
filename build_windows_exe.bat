@echo off
setlocal EnableExtensions

set "PROJECT_DIR=%~dp0"
set "VENV_DIR=%PROJECT_DIR%.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "BUILD_REQUIREMENTS=%PROJECT_DIR%requirements-build.txt"
set "APP=%PROJECT_DIR%insults.py"
set "DATA=%PROJECT_DIR%trump.json;."

cd /d "%PROJECT_DIR%"

if not exist "%VENV_PYTHON%" (
    call "%PROJECT_DIR%run_insult_generator.bat" --help
    if errorlevel 1 exit /b 1
)

"%VENV_PYTHON%" -m pip install --disable-pip-version-check -r "%BUILD_REQUIREMENTS%"
if errorlevel 1 (
    echo Failed to install build dependencies.
    exit /b 1
)

"%VENV_PYTHON%" -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
    --name TrumpInsultGenerator ^
    --add-data "%DATA%" ^
    "%APP%"
if errorlevel 1 (
    echo Failed to build TrumpInsultGenerator.exe.
    exit /b 1
)

echo Built dist\TrumpInsultGenerator.exe
