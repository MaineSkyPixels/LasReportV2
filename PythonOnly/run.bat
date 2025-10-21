@echo off
REM LAS File Analysis Tool - Windows Batch Runner
REM This script runs the application with the current Python interpreter

echo.
echo ========================================
echo   LAS File Analysis Tool
echo ========================================
echo.

python main.py

if errorlevel 1 (
    echo.
    echo Error: Failed to run the application.
    echo Make sure Python 3.12+ is installed and in PATH.
    echo.
    pause
)

