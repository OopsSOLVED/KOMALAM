@echo off
setlocal enabledelayedexpansion
title KOMALAM - Setup
color 0A

echo ============================================================
echo              KOMALAM - Local AI Chatbot Setup
echo ============================================================
echo.

:: ---- Check for Python ----
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://python.org
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo    Found Python %PYVER%

:: ---- Check/Install Ollama ----
echo.
echo [2/6] Checking Ollama installation...
where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo    Ollama not found. Downloading and installing...
    echo    This may take a few minutes...
    
    :: Download Ollama installer
    powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://ollama.com/download/OllamaSetup.exe' -OutFile '%TEMP%\OllamaSetup.exe' }"
    
    if not exist "%TEMP%\OllamaSetup.exe" (
        echo ERROR: Failed to download Ollama installer.
        echo Please check your internet connection and try again.
        pause
        exit /b 1
    )
    
    echo    Running Ollama installer...
    start /wait "" "%TEMP%\OllamaSetup.exe" /VERYSILENT /NORESTART
    
    :: Refresh PATH
    set "PATH=%LOCALAPPDATA%\Programs\Ollama;%PATH%"
    
    :: Clean up
    del "%TEMP%\OllamaSetup.exe" >nul 2>&1
    
    where ollama >nul 2>&1
    if %errorlevel% neq 0 (
        echo ERROR: Ollama installation may have failed.
        echo Please install manually from https://ollama.com
        pause
        exit /b 1
    )
    echo    Ollama installed successfully!
) else (
    echo    Ollama is already installed.
)

:: ---- Create Virtual Environment ----
echo.
echo [3/6] Creating Python virtual environment...
if not exist "venv" (
    python -m venv venv
    echo    Virtual environment created.
) else (
    echo    Virtual environment already exists.
)

:: ---- Install Dependencies ----
echo.
echo [4/6] Installing Python dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)
echo    Dependencies installed successfully!

:: ---- Start Ollama and Pull Model ----
echo.
echo [5/6] Pulling default AI model (llama3.2)...
echo    This download is ~2GB and may take several minutes...

:: Start Ollama service in background
start "" /B ollama serve >nul 2>&1
timeout /t 3 /nobreak >nul

ollama pull llama3.2
if %errorlevel% neq 0 (
    echo WARNING: Could not pull llama3.2 model.
    echo You can pull it later with: ollama pull llama3.2
) else (
    echo    Model llama3.2 ready!
)

:: ---- Pre-download Embedding Model ----
echo.
echo [6/6] Pre-downloading embedding model for memory system...
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2'); print('    Embedding model ready!')"

:: ---- Create data directory ----
if not exist "data" mkdir data
if not exist "data\faiss_index" mkdir data\faiss_index

echo.
echo ============================================================
echo              KOMALAM Setup Complete!
echo ============================================================
echo.
echo To launch KOMALAM, double-click 'launch.bat'
echo or run: launch.bat
echo.
pause
