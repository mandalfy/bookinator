@echo off
setlocal

:: Bookinator v2 Windows Run Script
:: --------------------------------

set "VENV_DIR=venv"

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Python not found. Please install Python 3.
    pause
    exit /b 1
)

:: Create venv if needed
if not exist "%VENV_DIR%" (
    echo [!] Creating virtual environment...
    python -m venv %VENV_DIR%
)

:: Activate venv
call %VENV_DIR%\Scripts\activate

:: Install dependencies
if exist requirements.txt (
    echo [!] Installing dependencies...
    pip install -q -r requirements.txt
) else (
    echo [!] requirements.txt not found. Installing manually...
    pip install -q flask requests ddgs
)

:: Run the app
echo.
echo [!] Starting Bookinator v2...
echo     Open: http://127.0.0.1:5000
echo.
python app.py

pause
