@echo off
REM Builds a standalone dist\ImageConverter.exe
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe call setup.bat
call .venv\Scripts\pip install pyinstaller
call .venv\Scripts\pyinstaller --noconfirm --onefile --windowed --name ImageConverter --icon=icon.ico --add-data "icon.ico;." --collect-all tkinterdnd2 --collect-all pillow_heif dng_to_jpg.py
echo Done: dist\ImageConverter.exe
pause
