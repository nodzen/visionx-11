@echo off
title VisionX-11 Installer
echo ===================================================
echo   VISIONX-11: INSTALLATION & SETUP
echo ===================================================

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERR] Python not found! Please install Python 3.10+
    pause
    exit /b
)

:: 2. Create Virtual Environment
if not exist "venv" (
    echo [1/3] Creating Python Virtual Environment...
    python -m venv venv
) else (
    echo [1/3] Virtual Environment already exists.
)

:: 3. Install Python Dependencies
echo [2/3] Installing Backend Dependencies...
call .\venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r backend_native/requirements.txt
if %errorlevel% neq 0 (
    echo [ERR] Failed to install Python dependencies.
    pause
    exit /b
)

:: 4. Install Frontend Dependencies
echo [3/3] Installing Frontend Dependencies (Node.js)...
cd frontend_react
npm install
if %errorlevel% neq 0 (
    echo [WARN] npm install failed. Make sure Node.js is installed.
)
cd ..

echo ===================================================
echo   INSTALLATION COMPLETE!
echo   Run 'run_native.bat' to start the system.
echo ===================================================
pause
