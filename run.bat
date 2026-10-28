@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\pythonw.exe call setup.bat
start "" .venv\Scripts\pythonw.exe dng_to_jpg.py
