@echo off
REM One-time setup: creates a virtual environment and installs everything.
cd /d "%~dp0"
python -m venv .venv || (echo Python install korun: https://www.python.org/downloads/ & pause & exit /b 1)
call .venv\Scripts\python -m pip install --upgrade pip
call .venv\Scripts\pip install -r requirements.txt
echo.
echo Setup done! Ekhon run.bat e double-click korun.
pause
