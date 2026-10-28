"""Image Converter - DNG/RAW/HEIC/PNG/WEBP/... to JPG/PNG/WEBP/TIFF/BMP/PDF."""
import io
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
import rawpy
from PIL import Image, ImageEnhance, ImageOps

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    BaseTk = TkinterDnD.Tk
except Exception:  # drag & drop optional
    DND_FILES = None
    BaseTk = tk.Tk

try:  # HEIC / HEIF / AVIF support
    import pillow_heif
    pillow_heif.register_heif_opener()
    try:
        pillow_heif.register_avif_opener()
    except Exception:
        pass
except Exception:
    pillow_heif = None

RAW_EXT = {".dng", ".cr2", ".cr3", ".crw", ".nef", ".nrw", ".arw", ".srf", ".sr2", ".raf",
           ".orf", ".rw2", ".pef", ".srw", ".x3f", ".3fr", ".iiq", ".erf", ".mef", ".mos",
           ".kdc", ".dcr", ".rwl", ".raw"}
IMG_EXT = {".heic", ".heif", ".avif", ".jpg", ".jpeg", ".jfif", ".png", ".webp", ".bmp",
           ".tif", ".tiff", ".gif", ".ico", ".tga", ".ppm", ".pgm", ".pbm", ".psd", ".jp2", ".dds"}
ALL_EXT = RAW_EXT | IMG_EXT
# name -> (Pillow format, extension)
OUT_FORMATS = {"JPG": ("JPEG", ".jpg"), "PNG": ("PNG", ".png"), "WEBP": ("WEBP", ".webp"),
               "TIFF": ("TIFF", ".tif"), "BMP": ("BMP", ".bmp"), "PDF": ("PDF", ".pdf"),
               "GIF": ("GIF", ".gif"), "ICO": ("ICO", ".ico")}
if pillow_heif:
    OUT_FORMATS["HEIC"] = ("HEIF", ".heic")


def baseline_exposure(src):
    """DNG BaselineExposure tag (iPhone ProRAW etc. use it)."""
    try:
        with Image.open(src) as im:
            return float(im.tag_v2.get(50730) or 0)
    except Exception:
        return 0.0


def develop(src, brightness=1.0):
    with rawpy.imread(src) as raw:
        lin = raw.postprocess(use_camera_wb=True, no_auto_bright=True,
                              gamma=(1, 1), output_bps=16).astype(np.float32) / 65535
    lin *= 2 ** baseline_exposure(src)

    # Auto exposure: bring average scene brightness to mid-grey
    lum = 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]
    key = np.exp(np.mean(np.log(lum[::4, ::4] + 1e-4)))
    lin *= np.clip(0.18 / key, 1, 8) * brightness

    # Soft highlight roll-off so bright areas don't clip harshly
    w = 4.0
    lin = np.clip(lin * (1 + lin / (w * w)) / (1 + lin) * 1.25, 0, 1)

    # sRGB gamma + gentle contrast curve
    s = np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * np.power(lin, 1 / 2.4) - 0.055)
    s = 0.75 * s + 0.25 * (s * s * (3 - 2 * s))
    img = Image.fromarray((np.clip(s, 0, 1) * 255 + 0.5).astype(np.uint8))
    return ImageEnhance.Color(img).enhance(1.1)


def scan_jpegs(src):
    """Find the largest JPEG stored anywhere inside the file.
    Works even when LibRaw can't read the DNG (e.g. JPEG-XL compressed ProRAW)."""
    with open(src, "rb") as fh:
        data = fh.read()
    best, pos = None, 0
    while True:
        pos = data.find(b"\xff\xd8\xff", pos)
        if pos < 0:
            break
        try:
            img = Image.open(io.BytesIO(data[pos:]))
            if img.format == "JPEG" and (best is None or img.size[0] * img.size[1] > best.size[0] * best.size[1]):
                img.load()
                best = img
        except Exception:
            pass
        pos += 3
    return best


def plain_image(src):
    """Some '.DNG' files are really normal JPG/PNG photos with a wrong name."""
    with open(src, "rb") as fh:
        head = fh.read(8)
    if head[:3] == b"\xff\xd8\xff" or head[:8] == b"\x89PNG\r\n\x1a\n":
        img = Image.open(src)
        img.load()
        return img
    return None


def embedded_preview(src):
    """Camera's own full-size JPEG inside the DNG (iPhone ProRAW, many others).
    This is exactly what Windows Photos / the phone shows."""
    img = plain_image(src)
    if img is not None:
        meta = {k: img.info[k] for k in ("exif", "icc_profile") if img.info.get(k)}
        return ImageOps.exif_transpose(img).convert("RGB"), meta
    try:
        with rawpy.imread(src) as raw:
            full_w = raw.sizes.width
            thumb = raw.extract_thumb()
        if thumb.format != rawpy.ThumbFormat.JPEG:
            return None
        img = Image.open(io.BytesIO(thumb.data))
        if max(img.size) < 0.9 * full_w:  # small thumbnail only, not usable
            return None
    except rawpy.LibRawFileUnsupportedError:
        img = scan_jpegs(src)  # LibRaw can't decode this DNG
        if img is None or max(img.size) < 1000:
            raise ValueError("Ei DNG format support kore na, ar bhitore kono boro preview o nei")
    except Exception:
        return None
    meta = {k: img.info[k] for k in ("exif", "icc_profile") if img.info.get(k)}
    img = ImageOps.exif_transpose(img).convert("RGB")
    return img, meta


def load_image(src, brightness):
    """Return (PIL image, metadata) for any supported input file."""
    if os.path.splitext(src)[1].lower() in RAW_EXT:
        preview = embedded_preview(src)
        if preview:
            img, meta = preview
        else:
            return develop(src, brightness), {}
    else:
        img = Image.open(src)
        img.seek(0)  # first frame for GIF / multi-page TIFF
        meta = {k: img.info[k] for k in ("exif", "icc_profile") if img.info.get(k)}
        img = ImageOps.exif_transpose(img)
    if abs(brightness - 1.0) > 0.01:
        mode = img.mode
        img = ImageEnhance.Brightness(img.convert("RGBA" if "A" in mode else "RGB")).enhance(brightness)
    return img, meta


def flatten(img):
    """Drop transparency onto white (for JPG/BMP/PDF)."""
    if img.mode in ("RGBA", "LA", "PA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        return bg
    return img.convert("RGB")


def convert_file(src, out_dir, quality, brightness, out_fmt="JPG"):
    pil_fmt, ext = OUT_FORMATS[out_fmt]
    base = os.path.join(out_dir, os.path.splitext(os.path.basename(src))[0])
    dst, n = base + ext, 1
    while os.path.exists(dst):  # don't overwrite same-named files
        dst = f"{base}_{n}{ext}"
        n += 1
    img, meta = load_image(src, brightness)
    kw = {}
    if pil_fmt == "JPEG":
        img, kw = flatten(img), dict(meta, quality=quality, optimize=True, subsampling=0)
    elif pil_fmt == "PNG":
        img = img if img.mode in ("RGB", "RGBA", "L", "LA", "P") else img.convert("RGBA")
        kw = dict(meta, optimize=True)
    elif pil_fmt == "WEBP":
        img = img.convert("RGBA" if "A" in img.mode else "RGB")
        kw = dict(meta, quality=quality, method=6)
    elif pil_fmt == "HEIF":
        img = img.convert("RGBA" if "A" in img.mode else "RGB")
        kw = dict(meta, quality=quality)
    elif pil_fmt == "TIFF":
        img = img.convert("RGBA" if "A" in img.mode else "RGB")
        kw = dict(meta, compression="tiff_lzw")
    elif pil_fmt in ("BMP", "PDF"):
        img = flatten(img)
        if pil_fmt == "PDF":
            kw = {"resolution": 300}
    elif pil_fmt == "GIF":
        img = img.convert("RGBA" if "A" in img.mode else "RGB")
    elif pil_fmt == "ICO":
        img = img.convert("RGBA")
        img.thumbnail((256, 256))
        kw = {"sizes": [(s, s) for s in (16, 32, 48, 64, 128, 256) if s <= max(img.size)]}
    img.save(dst, pil_fmt, **kw)
    return dst


class App(BaseTk):
    def __init__(self):
        super().__init__()
        self.title("Image Converter (DNG / RAW / HEIC / PNG / WEBP ...)")
        try:
            here = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
            self.iconbitmap(os.path.join(here, "icon.ico"))
        except Exception:
            pass
        self.geometry("620x560")
        self.minsize(520, 480)
        self.files = []
        self.quality = tk.IntVar(value=95)
        self.bright = tk.DoubleVar(value=1.0)
        self.out_fmt = tk.StringVar(value="JPG")

        pad = {"padx": 10, "pady": 5}
        bar = ttk.Frame(self)
        bar.pack(fill="x", **pad)
        for text, cmd in (("+ File add", self.pick_files), ("+ Folder add", self.pick_folder),
                          ("Selected remove", self.remove_selected), ("Shob clear", self.clear)):
            ttk.Button(bar, text=text, command=cmd).pack(side="left", expand=True, fill="x", padx=2)

        self.count = ttk.Label(self, text="0 ta file  |  File/folder ekhane drag & drop o korte paren")
        self.count.pack(**pad)
        box = ttk.Frame(self)
        box.pack(fill="both", expand=True, **pad)
        self.listbox = tk.Listbox(box, selectmode="extended")
        sb = ttk.Scrollbar(box, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<Delete>", lambda e: self.remove_selected())

        if DND_FILES:
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", lambda e: self.add_paths(self.tk.splitlist(e.data)))

        self.qlabel = self.slider("JPG Quality:", self.quality, 50, 100, lambda v: str(int(float(v))))
        self.blabel = self.slider("Brightness:", self.bright, 0.5, 2.0, lambda v: f"{float(v):.2f}")

        row = ttk.Frame(self)
        row.pack(fill="x", padx=10, pady=5)
        ttk.Label(row, text="Output format:", width=12).pack(side="left")
        ttk.Combobox(row, textvariable=self.out_fmt, values=list(OUT_FORMATS),
                     state="readonly", width=8).pack(side="left", padx=5)
        if not pillow_heif:
            ttk.Label(row, text="(HEIC er jonno: pip install pillow-heif)").pack(side="left")

        self.progress = ttk.Progressbar(self)
        self.progress.pack(fill="x", **pad)
        self.status = ttk.Label(self, text="Ready")
        self.status.pack(**pad)
        self.btn = ttk.Button(self, text="Convert", command=self.start)
        self.btn.pack(fill="x", **pad)

    def slider(self, text, var, lo, hi, fmt):
        row = ttk.Frame(self)
        row.pack(fill="x", padx=10, pady=5)
        ttk.Label(row, text=text, width=12).pack(side="left")
        label = ttk.Label(row, text=fmt(var.get()), width=5)
        ttk.Scale(row, from_=lo, to=hi, variable=var,
                  command=lambda v: label.config(text=fmt(v))).pack(side="left", fill="x", expand=True, padx=5)
        label.pack(side="left")
        return label

    def pick_files(self):
        files = filedialog.askopenfilenames(title="Image file select korun (Ctrl+A = shob)",
            filetypes=[("All supported", " ".join("*" + e for e in sorted(ALL_EXT))),
                       ("HEIC / HEIF / AVIF", "*.heic *.heif *.avif"),
                       ("RAW (DNG, CR2, NEF, ARW...)", " ".join("*" + e for e in sorted(RAW_EXT))),
                       ("All files", "*.*")])
        self.add_paths(files)

    def pick_folder(self):
        d = filedialog.askdirectory(title="Image ache emon folder select korun")
        if d:
            self.add_paths([d])

    def add_paths(self, paths):
        """Add files and folders (folders scanned with sub-folders); skip duplicates."""
        known = {os.path.normcase(f) for f in self.files}
        for p in paths:
            if os.path.isdir(p):
                found = [os.path.join(r, n) for r, _, names in os.walk(p) for n in sorted(names)]
            else:
                found = [p]
            for f in found:
                key = os.path.normcase(os.path.abspath(f))
                if os.path.splitext(f)[1].lower() in ALL_EXT and key not in known:
                    known.add(key)
                    self.files.append(f)
                    self.listbox.insert(tk.END, f)
        self.update_count()

    def remove_selected(self):
        for i in reversed(self.listbox.curselection()):
            self.listbox.delete(i)
            del self.files[i]
        self.update_count()

    def clear(self):
        self.files.clear()
        self.listbox.delete(0, tk.END)
        self.update_count()

    def update_count(self):
        self.count.config(text=f"{len(self.files)} ta file add kora hoyeche")

    def start(self):
        if not self.files:
            messagebox.showwarning("Warning", "Age file select korun.")
            return
        # Windows dialog e "New folder" button diye notun folder o banano jay
        out = filedialog.askdirectory(title="Converted file kothay save hobe? (New folder o banate paren)",
                                      initialdir=os.path.dirname(self.files[0]), mustexist=False)
        if not out:
            return
        os.makedirs(out, exist_ok=True)
        self.btn.config(state="disabled")
        self.progress.config(maximum=len(self.files), value=0)
        threading.Thread(target=self.run, args=(out, int(self.quality.get()), float(self.bright.get()), self.out_fmt.get()),
                         daemon=True).start()

    def run(self, out, quality, brightness, out_fmt):
        errors = []
        total = len(self.files)
        for i, f in enumerate(self.files, 1):
            self.after(0, self.status.config, {"text": f"Converting {i}/{total}: {os.path.basename(f)}"})
            try:
                convert_file(f, out, quality, brightness, out_fmt)
            except Exception as e:
                errors.append(f"{os.path.basename(f)}: {e}")
            self.after(0, self.progress.config, {"value": i})
        self.after(0, self.done, total - len(errors), errors, out)

    def done(self, ok, errors, out):
        self.btn.config(state="normal")
        self.status.config(text=f"Done! {ok} ta file convert hoyeche.")
        if errors:
            messagebox.showerror("Kichu error", "\n".join(errors[:20]))
        if messagebox.askyesno("Success", f"{ok} ta file convert hoyeche!\nFolder ta khulben?"):
            os.startfile(out)


if __name__ == "__main__":
    App().mainloop()
