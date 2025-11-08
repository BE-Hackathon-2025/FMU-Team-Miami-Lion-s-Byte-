@echo off
REM Quick Setup Script for Healthcare App

echo ========================================
echo Healthcare App Quick Setup
echo ========================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python found!
echo.

echo Creating virtual environment...
if exist venv (
    echo Virtual environment already exists
) else (
    python -m venv venv
    echo Virtual environment created
)
echo.

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing required packages...
pip install -r requirements.txt

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To run the app:
echo 1. venv\Scripts\activate
echo 2. python main.py
echo 3. Open browser to http://localhost:5000
echo.
pause
