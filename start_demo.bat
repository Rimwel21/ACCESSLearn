@echo off
title SIGNHEAR 1-Click Demo Launcher
echo ===================================================
echo   SIGNHEAR: Grade 4 E-Learning System
echo   Launching Backend and Frontend for Demo...
echo ===================================================

:: Step 0a: Ensure backend .env exists
if not exist ".env" (
    echo [Setup] Backend .env file missing. Creating from .env.example...
    copy .env.example .env >nul
)

:: Step 0b: Ensure frontend .env exists
if not exist "E-Learn\frontend\.env" (
    if exist "E-Learn\frontend\.env.example" (
        echo [Setup] Frontend .env file missing. Creating from .env.example...
        copy E-Learn\frontend\.env.example E-Learn\frontend\.env >nul
    )
)

:: Step 0c: Detect Python virtual environment or system Python
set PYTHON_EXE=python
if exist ".venv\Scripts\python.exe" set PYTHON_EXE=.venv\Scripts\python.exe
if exist "venv\Scripts\python.exe" set PYTHON_EXE=venv\Scripts\python.exe

:: Step 0d: Check frontend dependencies
if not exist "E-Learn\frontend\node_modules" (
    echo [Setup] Installing frontend dependencies (one-time setup)...
    pushd E-Learn\frontend
    call npm install
    popd
)

echo [1/3] Verifying and unlocking demo accounts...
%PYTHON_EXE% scripts\demo_account_check.py

echo [2/3] Starting FastAPI Backend on port 8000...
start "SIGNHEAR Backend" cmd /k "%PYTHON_EXE% -m uvicorn main:app --reload --port 8000"

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
