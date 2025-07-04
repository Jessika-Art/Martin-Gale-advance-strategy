@echo off
REM MartinGales Trading Bot Launcher
REM This batch file starts the application with proper signal handling

echo ========================================
echo    MartinGales Trading Bot Launcher
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if we're in the correct directory
if not exist "run_app.py" (
    echo ERROR: run_app.py not found
    echo Please run this batch file from the MartinGales directory
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist "env\Scripts\activate.bat" (
    echo Activating virtual environment...
    call env\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found at env\Scripts\activate.bat
    echo Running with system Python...
    echo.
)

REM Check if Streamlit is installed
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Streamlit is not installed
    echo Please install requirements: pip install -r requirements.txt
    pause
    exit /b 1
)

echo Starting MartinGales Trading Bot...
echo Press Ctrl+C to stop the application
echo.

REM Run the application with proper signal handling
python run_app.py

echo.
echo Application stopped.
pause