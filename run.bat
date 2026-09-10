@echo off
echo ===================================================
echo   🚀 Starting Satellite Cloud Removal Web Server
echo ===================================================

if exist venv (
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] venv folder not found! Running with system Python...
)

echo [INFO] Server running at http://127.0.0.1:5000
python sih.py
pause
