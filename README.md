# Image Converter (DNG / RAW / HEIC → JPG and more)

A simple desktop app (Tkinter) for batch image conversion. Supports drag & drop, folders (with sub-folders), quality and brightness sliders.

**Input:** HEIC, HEIF, AVIF, DNG and other RAW (CR2, CR3, NEF, ARW, RAF, ORF, RW2, PEF, SRW...), JPG, PNG, WEBP, BMP, TIFF, GIF, ICO, TGA, PSD, JP2, PPM

**Output:** JPG, PNG, WEBP, TIFF, BMP, PDF, GIF, ICO, HEIC

RAW files use the camera's embedded full-size preview when available, otherwise they are developed with auto exposure and a soft highlight roll-off. Transparent images are flattened onto white for JPG/BMP/PDF.

## Notun PC / local delete korar por abar shuru

Shob code GitHub e ache, tai local folder delete korleo kono problem nei:

```bash
git clone https://github.com/devsuvo/dngtojpg-converter.git
cd dngtojpg-converter
```

Tarpor:

1. `setup.bat` e double-click (prothom bar, library install hobe)
2. `run.bat` e double-click (app chalu hobe)
3. `.exe` banate chaile `build_exe.bat` (file ashbe `dist\ImageConverter.exe` e)

Manual vabe: `pip install -r requirements.txt` tarpor `python dng_to_jpg.py`

## Update kore GitHub e pathano

```bash
git pull                     # age latest code nin
# ...code change korun...
git add .
git commit -m "ki change korlen"
git push
```

> Notun library use korle `requirements.txt` e tar naam likhe din, noile clone korar por install hobe na.

## Requirements

Python 3.8+, `rawpy`, `Pillow`, `numpy`, `pillow-heif` (HEIC/AVIF), `tkinterdnd2` (optional, for drag & drop).
