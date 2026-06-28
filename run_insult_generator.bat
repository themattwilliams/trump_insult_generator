@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "PROJECT_DIR=%~dp0"
set "VENV_DIR=%PROJECT_DIR%.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "REQUIREMENTS=%PROJECT_DIR%requirements.txt"
set "REQUIREMENTS_HASH_FILE=%VENV_DIR%\requirements.sha256"
set "APP=%PROJECT_DIR%insults.py"
set "NEEDS_INSTALL=0"

cd /d "%PROJECT_DIR%"

if not exist "%VENV_PYTHON%" (
    echo Creating project virtual environment...
    py -3 -m venv "%VENV_DIR%"
    if errorlevel 1 (
        python -m venv "%VENV_DIR%"
    )
    if errorlevel 1 (
        echo Failed to create virtual environment.
        exit /b 1
    )
    set "NEEDS_INSTALL=1"
)

call :hash_requirements
if errorlevel 1 exit /b 1

if not exist "%REQUIREMENTS_HASH_FILE%" (
    set "NEEDS_INSTALL=1"
) else (
    set /p "SAVED_REQUIREMENTS_HASH="<"%REQUIREMENTS_HASH_FILE%"
    if /I not "!CURRENT_REQUIREMENTS_HASH!"=="!SAVED_REQUIREMENTS_HASH!" (
        set "NEEDS_INSTALL=1"
    )
)

if "%NEEDS_INSTALL%"=="1" goto dependencies_changed
goto dependencies_current

:dependencies_changed
echo Installing dependencies from requirements.txt...
"%VENV_PYTHON%" -m pip install --disable-pip-version-check -r "%REQUIREMENTS%"
if errorlevel 1 (
    echo Failed to install dependencies from requirements.txt.
    exit /b 1
)
>"%REQUIREMENTS_HASH_FILE%" echo !CURRENT_REQUIREMENTS_HASH!
goto launch_app

:dependencies_current
echo Dependencies are current.
goto launch_app

:launch_app
"%VENV_PYTHON%" "%APP%" %*
exit /b %errorlevel%

:hash_requirements
if not exist "%REQUIREMENTS%" (
    echo Missing requirements.txt.
    exit /b 1
)

set "CURRENT_REQUIREMENTS_HASH="
for /f "skip=1 tokens=* delims=" %%H in ('certutil -hashfile "%REQUIREMENTS%" SHA256') do (
    if not defined CURRENT_REQUIREMENTS_HASH (
        set "CURRENT_REQUIREMENTS_HASH=%%H"
    )
)

if not defined CURRENT_REQUIREMENTS_HASH (
    echo Failed to hash requirements.txt.
    exit /b 1
)

exit /b 0
