@echo off
REM Artha Stock Market Learning Simulator - One-Click Installer (Windows)
REM This script sets up the complete development environment automatically

setlocal enabledelayedexpansion

echo ================================
echo Artha Stock Market Simulator - Installer
echo ================================
echo.

REM Check Python version
echo [INFO] Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.12+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [SUCCESS] Python %PYTHON_VERSION% detected
echo.

REM Setup virtual environment
echo ================================
echo Setting up Virtual Environment
echo ================================
echo.

if exist ".venv" (
    echo [INFO] Virtual environment already exists at .venv
) else (
    echo [INFO] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created
)
echo.

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [SUCCESS] Virtual environment activated
echo.

REM Ensure pip is available
echo ================================
echo Ensuring pip is available
echo ================================
echo.

echo [INFO] Upgrading pip to latest version...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERROR] Failed to upgrade pip
    pause
    exit /b 1
)
echo [SUCCESS] pip is ready
echo.

REM Install UV package manager
echo ================================
echo Installing UV Package Manager
echo ================================
echo.

where uv >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing UV...
    pip install uv
    if errorlevel 1 (
        echo [ERROR] Failed to install UV
        pause
        exit /b 1
    )
    echo [SUCCESS] UV installed successfully
) else (
    echo [INFO] UV is already installed
    echo [SUCCESS] UV is ready
)
echo.

REM Install dependencies
echo ================================
echo Installing Project Dependencies
echo ================================
echo.

if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found!
    pause
    exit /b 1
)

echo [INFO] Installing dependencies from requirements.txt using UV...
uv pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [SUCCESS] All dependencies installed successfully
echo.

REM Verify installation
echo ================================
echo Verifying Installation
echo ================================
echo.

python -c "import textual" 2>nul && (
    echo [SUCCESS] textual is installed
) || (
    echo [WARNING] textual might not be installed correctly
)

python -c "import dspy" 2>nul && (
    echo [SUCCESS] dspy is installed
) || (
    echo [WARNING] dspy might not be installed correctly
)

python -c "import sqlalchemy" 2>nul && (
    echo [SUCCESS] sqlalchemy is installed
) || (
    echo [WARNING] sqlalchemy might not be installed correctly
)

python -c "import yfinance" 2>nul && (
    echo [SUCCESS] yfinance is installed
) || (
    echo [WARNING] yfinance might not be installed correctly
)

echo.

REM Setup data directories
echo ================================
echo Setting up Data Directories
echo ================================
echo.

if not exist "data" mkdir data
if not exist "data\cache" mkdir data\cache
echo [SUCCESS] Data directories created
echo.

REM Check for Ollama (optional)
echo ================================
echo Checking Optional Dependencies
echo ================================
echo.

where ollama >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Ollama is not installed (AI Coach will use fallback mode)
    echo [INFO] To install Ollama: Download from https://ollama.ai/download
) else (
    echo [SUCCESS] Ollama is installed (AI Coach will work)

    ollama list | findstr "qwen3:8b" >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] qwen3:8b model not found. AI Coach will use fallback mode.
        echo [INFO] To install: ollama pull qwen3:8b
    ) else (
        echo [SUCCESS] qwen3:8b model is available
    )
)
echo.

REM Installation complete
echo ================================
echo Installation Complete!
echo ================================
echo.
echo Artha is ready to run!
echo.
echo To start playing:
echo   1. Activate the virtual environment:
echo      .venv\Scripts\activate.bat
echo.
echo   2. Run the game:
echo      python -m src.main
echo.
echo Optional - For AI Coach support:
echo   1. Install Ollama from https://ollama.ai/download
echo   2. Pull model: ollama pull qwen3:8b
echo   3. Start Ollama: ollama serve
echo.
echo Happy trading!
echo.

pause
