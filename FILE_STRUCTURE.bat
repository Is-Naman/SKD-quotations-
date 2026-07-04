@echo off
echo.
echo =====================================================
echo Quotation Automation System - File Structure
echo =====================================================
echo.

echo Core System Files:
echo   - quotation_automation.py   (Automation engine)
echo   - app.py                    (Flask web server)
echo   - config.py                 (Configuration)
echo   - utils.py                  (Helper utilities)
echo.

echo Frontend:
echo   - templates/index.html      (Web interface)
echo.

echo Configuration:
echo   - requirements.txt          (Python dependencies)
echo   - .gitignore               (Git ignore rules)
echo.

echo Documentation:
echo   - README.md                 (Complete guide)
echo   - QUICKSTART.md            (Quick start guide)
echo.

echo Startup Scripts:
echo   - run_web.ps1              (PowerShell - Windows)
echo   - run_web.bat              (Batch - Windows CMD)
echo   - run_web.sh               (Bash - Linux/macOS)
echo   - setup.py                 (Automatic setup)
echo.

echo Sample Files:
echo   - product_catalog_sample.csv   (Catalog template)
echo   - sample_enquiry.txt           (Enquiry example)
echo.

echo Runtime Directories (auto-created):
echo   - venv/                    (Virtual environment)
echo   - uploads/                 (Uploaded files)
echo   - catalogs/                (Stored catalogs)
echo.

echo =====================================================
echo To get started, run:
echo   python setup.py
echo Or manually:
echo   python -m venv venv
echo   venv\Scripts\activate
echo   pip install -r requirements.txt
echo   python app.py
echo =====================================================
echo.
