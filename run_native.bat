@echo off
title VisionX-11 Launcher
echo ===================================================
echo   VISIONX-11: TRUE NATIVE AI VISION SYSTEM
echo ===================================================

:: 1. Force kill existing sessions by window title
echo [1/3] Cleaning up active windows...
taskkill /F /FI "WINDOWTITLE eq YOLO_*" /T >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq VisionX-11 Launcher" /T >nul 2>&1
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1

echo [2/3] Preparing Neural Core...
ping 127.0.0.1 -n 2 >nul
echo.

:: 3. Launching systems
echo [3/3] Launching Neural Backend...
start "YOLO_BACKEND" cmd /k "title YOLO_BACKEND && .\venv\Scripts\python.exe -m backend_native.main"

echo [3/3] Launching Cyber Dashboard...
cd frontend_react
start "YOLO_FRONTEND" cmd /c "title YOLO_FRONTEND && npm run dev -- --port 5173"
cd ..

echo ===================================================
echo   ALL SYSTEMS LAUNCHED (SECURE MODE)
echo.
echo   [FRONTEND] https://localhost:5173
echo   [IPHONE]   https://192.168.0.4:5173
echo.
echo   [!] IMPORTANT: You MUST use HTTPS in the address bar!
echo   [!] Accept the "Not Secure" warning in Safari/Chrome.
echo ===================================================
pause
