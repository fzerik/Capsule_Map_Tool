@echo off
setlocal
cd /d "%~dp0"
set "LOG_LEVEL=INFO"
set "FLASK_DEBUG=false"

echo Starting Capsule Map Tool...

if exist "venv\Scripts\python.exe" (
    set "PYTHON_EXE=venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

%PYTHON_EXE% run.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Capsule Map Tool failed to start.
    pause
)
