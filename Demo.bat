@echo off
setlocal
cd /d "%~dp0"

rem Doi mat khau demo tai day neu muon. De trong thi moi lan chay sinh mat khau ngau nhien.
set "AB_USERNAME=demo"
set "AB_PASSWORD="

if not exist ".venv\Scripts\python.exe" (
    echo Thieu moi truong .venv. Xem README.md de cai dat.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -X utf8 -u scripts\start_demo.py
pause
