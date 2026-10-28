# DNG to JPG Converter

A simple desktop app (Tkinter) that converts DNG / RAW photos to JPG with automatic exposure, soft highlight roll-off and a gentle contrast curve. Supports drag & drop.

## Setup

```bash
git clone https://github.com/devsuvo/dngtojpg-converter.git
cd dngtojpg-converter
pip install -r requirements.txt
```

## Run

```bash
python dng_to_jpg.py
```

## Build a Windows .exe (optional)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=icon.ico --collect-all tkinterdnd2 dng_to_jpg.py
```

## Update workflow

```bash
git pull          # get latest changes
# ...edit code...
git add .
git commit -m "your message"
git push
```

## Requirements

Python 3.8+, `rawpy`, `Pillow`, `numpy`, `tkinterdnd2` (optional, for drag & drop).
