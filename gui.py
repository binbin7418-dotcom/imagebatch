#!/usr/bin/env python3
"""ImageBatch desktop shell (tkinter). Pick a folder -> marketplace-ready images."""
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from image_batch import process_folder, PRESETS


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ImageBatch — Marketplace Image Prep")
        self.geometry("680x560")
        self.src = tk.StringVar()
        self.preset = tk.StringVar(value="shopify")
        self.fmt = tk.StringVar(value="jpg")
        self.prefix = tk.StringVar()
        tk.Label(self, text="Folder of product images:").pack(anchor="w", padx=12, pady=(12, 2))
        row = tk.Frame(self)
        row.pack(fill="x", padx=12)
        tk.Entry(row, textvariable=self.src).pack(side="left", fill="x", expand=True)
        tk.Button(row, text="Browse…", command=self.pick).pack(side="left", padx=6)
        tk.Label(self, text="Platform preset:").pack(anchor="w", padx=12, pady=(10, 0))
        for key, p in PRESETS.items():
            tk.Radiobutton(self, text=p["label"], variable=self.preset, value=key).pack(anchor="w", padx=20)
        row2 = tk.Frame(self)
        row2.pack(fill="x", padx=12, pady=(10, 0))
        tk.Label(row2, text="Output format:").pack(side="left")
        for f in ("jpg", "png", "webp"):
            tk.Radiobutton(row2, text=f.upper(), variable=self.fmt, value=f).pack(side="left")
        tk.Label(row2, text="   File name prefix (optional):").pack(side="left")
        tk.Entry(row2, textvariable=self.prefix, width=18).pack(side="left")
        self.btn = tk.Button(self, text="Process Images", command=self.run, height=2)
        self.btn.pack(pady=12)
        self.log = scrolledtext.ScrolledText(self, wrap="word")
        self.log.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.write("ImageBatch orients, resizes, converts and de-metas a whole folder\n"
                   "of product photos to a marketplace preset. Originals are never\n"
                   "touched, and everything runs locally on this computer.\n")

    def write(self, s):
        self.log.insert("end", s)
        self.log.see("end")

    def pick(self):
        p = filedialog.askdirectory()
        if p:
            self.src.set(p)

    def run(self):
        src = self.src.get().strip()
        if not src or not os.path.isdir(src):
            messagebox.showerror("ImageBatch", "Choose an image folder first.")
            return
        self.btn.config(state="disabled")
        threading.Thread(target=self._work, args=(src,), daemon=True).start()

    def _work(self, src):
        try:
            outdir = os.path.join(src, "imagebatch_output")
            s = process_folder(src, outdir, self.preset.get(), self.fmt.get(),
                               prefix=self.prefix.get().strip())
            self.write(f"\nDone. Processed {s['processed']} of {s['found']} images · "
                       f"total size {s['saved_pct']}% smaller · warnings: {s['warnings']}\n"
                       f"Output folder: {s['outdir']}\nReport: {s['report_path']}\n")
        except Exception as e:
            self.write(f"\nError: {e}\n")
        finally:
            self.btn.config(state="normal")


if __name__ == "__main__":
    App().mainloop()
