#!/bin/bash

# MartinGales Trading Bot Launcher
# This script starts the application with proper signal handling

echo "========================================"
echo "    MartinGales Trading Bot Launcher"
echo "========================================"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "ERROR: Python is not installed or not in PATH"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

# Check if we're in the correct directory
if [ ! -f "run_app.py" ]; then
    echo "ERROR: run_app.py not found"
    echo "Please run this script from the MartinGales directory"
    exit 1
fi

# Check if virtual environment exists
if [ -f "env/bin/activate" ]; then
    echo "Activating virtual environment..."
    source env/bin/activate
else
    echo "WARNING: Virtual environment not found at env/bin/activate"
    echo "Running with system Python..."
    echo
fi

# Check if Streamlit is installed
if ! $PYTHON_CMD -c "import streamlit" &> /dev/null; then
    echo "ERROR: Streamlit is not installed"
    echo "Please install requirements: pip install -r requirements.txt"
    exit 1
fi

echo "Starting MartinGales Trading Bot..."
echo "Press Ctrl+C to stop the application"
echo

# Run the application with proper signal handling
$PYTHON_CMD run_app.py

echo
echo "Application stopped."