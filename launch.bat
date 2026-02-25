@echo off
title KOMALAM - Local AI Chatbot
color 0B

echo ============================================================
echo              KOMALAM - Starting...
echo ============================================================
echo.

:: Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found.
    echo Please run setup.bat first.
    pause
    exit /b 1
)

:: Start Ollama service if not running
tasklist /FI "IMAGENAME eq ollama.exe" 2>nul | find /I "ollama.exe" >nul
if %errorlevel% neq 0 (
    echo Starting Ollama service...
    start "" /B ollama serve >nul 2>&1
    timeout /t 3 /nobreak >nul
) else (
    echo Ollama service is already running.
)

:: Activate venv and launch
call venv\Scripts\activate.bat
echo Launching KOMALAM...
python main.py

pause
