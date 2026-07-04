@echo off
REM Quick start batch script for Windows Command Prompt users

echo.
echo ========================================
echo Quotation Automation - Quick Start
echo ========================================
echo.

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt > nul 2>&1

echo.
echo ========================================
echo Starting web application...
echo ========================================
echo.
echo Open your browser: http://localhost:5000
echo.

python app.py
