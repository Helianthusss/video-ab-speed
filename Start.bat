@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Missing Windows virtual environment: .venv\Scripts\python.exe
    echo See README.md for setup instructions.
    pause
    exit /b 1
)
if not defined AB_PORT set "AB_PORT=8765"
echo Open http://127.0.0.1:%AB_PORT% in your browser when the server is ready.
".venv\Scripts\python.exe" -X utf8 -m video_ab
if errorlevel 1 pause
