@echo off
title SIGNHEAR 1-Click Demo Launcher
echo ===================================================
echo   SIGNHEAR: Grade 4 E-Learning System
echo   Launching Backend and Frontend for Demo...
echo ===================================================

echo [1/3] Verifying and unlocking demo accounts...
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe scripts\demo_account_check.py
) else (
    python scripts\demo_account_check.py
)

echo [2/3] Starting FastAPI Backend on port 8000...
if exist ".venv\Scripts\python.exe" (
    start "SIGNHEAR Backend" cmd /k ".venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000"
) else (
    start "SIGNHEAR Backend" cmd /k "python -m uvicorn main:app --reload --port 8000"
)

echo [3/3] Starting Frontend on port 5173...
start "SIGNHEAR Frontend" cmd /k "cd E-Learn\frontend && npm run dev"

echo Waiting 5 seconds for servers to start...
timeout /t 5 /nobreak >nul

echo Opening browser at http://localhost:5173 ...
start http://localhost:5173

echo ===================================================
echo SIGNHEAR is now RUNNING!
echo Keep the backend and frontend terminal windows open.
echo To stop, simply close the two opened terminal windows.
echo ===================================================
pause
