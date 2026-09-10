@echo off
echo ===================================================
echo   🛰️ Satellite Cloud Removal System Setup (SIH 2026)
echo ===================================================

if not exist venv (
    echo [INFO] Creating Python virtual environment...
    python -m venv venv
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Installing required dependencies...
pip install -r requirements.txt

echo ===================================================
echo [SUCCESS] Setup complete! You can now launch run.bat
echo ===================================================
pause
