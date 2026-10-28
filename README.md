# Image Converter (DNG / RAW / HEIC → JPG and more)

A simple desktop app (Tkinter) for batch image conversion. Supports drag & drop, folders (with sub-folders), quality and brightness sliders.

**Input:** HEIC, HEIF, AVIF, DNG and other RAW (CR2, CR3, NEF, ARW, RAF, ORF, RW2, PEF, SRW...), JPG, PNG, WEBP, BMP, TIFF, GIF, ICO, TGA, PSD, JP2, PPM

**Output:** JPG, PNG, WEBP, TIFF, BMP, PDF, GIF, ICO, HEIC

RAW files use the camera's embedded full-size preview when available, otherwise they are developed with auto exposure and a soft highlight roll-off. Transparent images are flattened onto white for JPG/BMP/PDF.

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
pyinstaller --onefile --windowed --icon=icon.ico --collect-all tkinterdnd2 --collect-all pillow_heif dng_to_jpg.py
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

Python 3.8+, `rawpy`, `Pillow`, `numpy`, `pillow-heif` (HEIC/AVIF), `tkinterdnd2` (optional, for drag & drop).
