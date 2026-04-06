"""
╔══════════════════════════════════════════════════════════╗
║         PC OPTIMIZER PRO — INSTALLER                     ║
║         github.com/Londopy/pc-optimizer                  ║
║                                                          ║
║  Pure Python installer — requires only Python 3.x        ║
║  (or nothing at all — downloads Python itself first)     ║
║                                                          ║
║  Run this file on any Windows machine:                   ║
║    python PCOptimizerPro_Installer.py                    ║
║  OR double-click if .py is associated with Python.       ║
╚══════════════════════════════════════════════════════════╝
"""

import sys
import os
import subprocess
import threading
import urllib.request
import urllib.error
import json
import zipfile
import shutil
import ctypes
import time
import re
import io
import platform
import winreg

# ── stdlib-only: tkinter for the GUI ──────────────────────
import tkinter as tk
from tkinter import ttk, messagebox

# ══════════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════════
APP_NAME        = "PC Optimizer Pro"
APP_VERSION     = "1.0.0"
GITHUB_USER     = "Londopy"
GITHUB_REPO     = "pc-optimizer"
GITHUB_BRANCH   = "main"
GITHUB_ZIP_URL  = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/archive/refs/heads/{GITHUB_BRANCH}.zip"
GITHUB_API_URL  = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"

PYTHON_VERSION  = "3.11.9"
PYTHON_URL      = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-amd64.exe"

DEFAULT_INSTALL = os.path.join(os.environ.get("PROGRAMFILES", "C:\\Program Files"), APP_NAME)

PACKAGES = [
    ("PyQt6",            "PyQt6>=6.6.0"),
    ("psutil",           "psutil>=5.9.0"),
    ("pynvml",           "pynvml>=11.5.0"),
    ("Pillow",           "Pillow>=10.0.0"),
    ("liquidctl",        "liquidctl>=1.13.0"),
    ("openrgb-python",   "openrgb-python>=0.2.13"),
    ("pywin32",          "pywin32>=306"),
    ("WMI",              "WMI>=1.5.1"),
]

# ══════════════════════════════════════════════════════════
#  COLOURS & FONTS  (all inline — no external assets)
# ══════════════════════════════════════════════════════════
C = {
    "bg":        "#090d12",
    "panel":     "#0d1117",
    "card":      "#111820",
    "border":    "#1e2733",
    "border2":   "#2a3441",
    "teal":      "#00d4aa",
    "teal_dim":  "#00a882",
    "teal_glow": "#00d4aa33",
    "white":     "#e8edf3",
    "grey":      "#8b9ab0",
    "dim":       "#3d4f63",
    "red":       "#f85149",
    "amber":     "#e3b341",
    "green":     "#3fb950",
    "text_sm":   "#6b7a8d",
}

# ══════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def elevate():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable,
            " ".join([f'"{a}"' for a in sys.argv]), None, 1
        )
        sys.exit(0)

def find_python():
    """Return path to a usable python.exe, or None."""
    for cmd in ("python", "python3", "py"):
        try:
            r = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=5)
            if r.returncode == 0 and "Python 3" in r.stdout + r.stderr:
                full = shutil.which(cmd)
                if full:
                    return full
        except Exception:
            pass
    # Check common install paths
    for path in [
        r"C:\Python311\python.exe",
        r"C:\Python310\python.exe",
        r"C:\Python312\python.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Python\Python311\python.exe"),
        os.path.expanduser(r"~\AppData\Local\Programs\Python\Python310\python.exe"),
        os.path.expanduser(r"~\AppData\Local\Programs\Python\Python312\python.exe"),
    ]:
        if os.path.isfile(path):
            return path
    return None

def get_python_version(exe):
    try:
        r = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=5)
        return (r.stdout + r.stderr).strip()
    except:
        return "Unknown"

def download_with_progress(url, dest, progress_cb=None, label_cb=None):
    """Download url → dest, calling progress_cb(pct) and label_cb(str)."""
    req = urllib.request.Request(url, headers={"User-Agent": "PCOptimizerPro-Installer/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        chunk = 65536
        with open(dest, "wb") as f:
            while True:
                data = resp.read(chunk)
                if not data:
                    break
                f.write(data)
                downloaded += len(data)
                if total and progress_cb:
                    progress_cb(downloaded / total * 100)
                if label_cb and total:
                    mb_done = downloaded / 1_048_576
                    mb_total = total / 1_048_576
                    label_cb(f"{mb_done:.1f} / {mb_total:.1f} MB")

# ══════════════════════════════════════════════════════════
#  ANIMATED CANVAS BACKGROUND
# ══════════════════════════════════════════════════════════
class ParticleCanvas(tk.Canvas):
    """Subtle animated particle field for the background."""
    import random as _rand

    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self._particles = []
        self._running = True
        self._build()
        self._animate()

    def _build(self):
        import random
        w, h = 900, 620
        for _ in range(28):
            x = random.uniform(0, w)
            y = random.uniform(0, h)
            r = random.uniform(0.8, 2.5)
            speed = random.uniform(0.15, 0.55)
            alpha = random.randint(30, 90)
            color = self._alpha_hex(alpha)
            cid = self.create_oval(x-r, y-r, x+r, y+r, fill=color, outline="")
            self._particles.append({"id": cid, "x": x, "y": y, "r": r,
                                     "vx": random.uniform(-0.3, 0.3),
                                     "vy": -speed, "a": alpha})

    def _alpha_hex(self, a):
        # Simulate alpha by blending teal with bg
        t = a / 255
        r = int(9 + (0 - 9) * t + 212 * t)
        g = int(13 + (0 - 13) * t + 212 * t)  # rough blend
        b = int(18 + (0 - 18) * t + 170 * t)
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _animate(self):
        if not self._running:
            return
        w, h = 900, 620
        for p in self._particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            if p["y"] < -10:
                p["y"] = h + 5
            if p["x"] < -10:
                p["x"] = w + 5
            if p["x"] > w + 10:
                p["x"] = -5
            r = p["r"]
            self.coords(p["id"], p["x"]-r, p["y"]-r, p["x"]+r, p["y"]+r)
        self.after(40, self._animate)

    def stop(self):
        self._running = False


# ══════════════════════════════════════════════════════════
#  MAIN INSTALLER UI
# ══════════════════════════════════════════════════════════
class InstallerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} — Installer")
        self.geometry("900x620")
        self.resizable(False, False)
        self.configure(bg=C["bg"])
        self.overrideredirect(True)          # Frameless

        # Centre on screen
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - 900) // 2
        y = (sh - 620) // 2
        self.geometry(f"900x620+{x}+{y}")

        self._drag_x = 0
        self._drag_y = 0
        self._install_dir = tk.StringVar(value=DEFAULT_INSTALL)
        self._create_shortcut = tk.BooleanVar(value=True)
        self._add_path = tk.BooleanVar(value=True)
        self._autostart = tk.BooleanVar(value=False)

        self._python_exe = None
        self._install_thread = None
        self._cancelled = False

        self._build_ui()
        self._check_python_async()

    # ── UI CONSTRUCTION ────────────────────────────────────
    def _build_ui(self):
        self._pages = {}

        # Root layout: left accent strip + right content
        self._root_frame = tk.Frame(self, bg=C["bg"])
        self._root_frame.place(x=0, y=0, width=900, height=620)

        # Animated particle background
        self._bg_canvas = ParticleCanvas(
            self._root_frame, width=900, height=620,
            bg=C["bg"], highlightthickness=0, bd=0
        )
        self._bg_canvas.place(x=0, y=0)

        # Outer border frame (gives a subtle glow border)
        border = tk.Frame(self._root_frame, bg=C["border"], bd=0)
        border.place(x=0, y=0, width=900, height=620)
        inner = tk.Frame(border, bg=C["bg"], bd=0)
        inner.place(x=1, y=1, width=898, height=618)

        # Left sidebar accent
        self._sidebar = tk.Frame(inner, bg=C["panel"], width=260, bd=0)
        self._sidebar.place(x=0, y=0, width=260, height=618)

        # Sidebar right border
        tk.Frame(inner, bg=C["border"], width=1).place(x=260, y=0, width=1, height=618)

        # Right content area
        self._content = tk.Frame(inner, bg=C["bg"], bd=0)
        self._content.place(x=261, y=0, width=637, height=618)

        self._build_sidebar()
        self._build_titlebar()
        self._build_pages()
        self._show_page("welcome")

    def _build_titlebar(self):
        """Drag handle + close button across the top of the right panel."""
        bar = tk.Frame(self._content, bg=C["bg"], height=44)
        bar.place(x=0, y=0, width=637, height=44)
        bar.bind("<ButtonPress-1>",   self._on_drag_start)
        bar.bind("<B1-Motion>",       self._on_drag)

        # Window control dots
        for col, cmd in [("#f85149", self.destroy), ("#febc2e", self._minimize),
                          ("#28c840", None)]:
            dot = tk.Label(bar, bg=C["bg"], width=2)
            dot.pack(side="right", padx=5, pady=14)
            c = tk.Canvas(bar, width=12, height=12, bg=C["bg"],
                          highlightthickness=0, bd=0)
            c.pack(side="right", pady=16)
            c.create_oval(0, 0, 11, 11, fill=col, outline="")
            if cmd:
                c.bind("<Button-1>", lambda e, fn=cmd: fn())
            c.bind("<Enter>", lambda e, cv=c, cl=col: cv.create_oval(
                0, 0, 11, 11, fill=self._lighten(cl), outline=""))
            c.bind("<Leave>", lambda e, cv=c, cl=col: cv.create_oval(
                0, 0, 11, 11, fill=cl, outline=""))

        # Divider
        tk.Frame(self._content, bg=C["border"], height=1).place(x=0, y=44, width=637, height=1)

    def _lighten(self, hexcol):
        r = min(255, int(hexcol[1:3], 16) + 30)
        g = min(255, int(hexcol[3:5], 16) + 30)
        b = min(255, int(hexcol[5:7], 16) + 30)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _build_sidebar(self):
        sb = self._sidebar

        # Logo area
        logo_frame = tk.Frame(sb, bg=C["panel"])
        logo_frame.place(x=0, y=0, width=260, height=90)

        # Teal accent bar at top of sidebar
        tk.Frame(logo_frame, bg=C["teal"], height=3).pack(fill="x")

        # App icon (drawn with canvas — no image file needed)
        icon_cv = tk.Canvas(logo_frame, width=44, height=44,
                            bg=C["panel"], highlightthickness=0)
        icon_cv.pack(pady=(14, 0))
        self._draw_icon(icon_cv, 22, 22, 20)

        tk.Label(logo_frame, text=APP_NAME.upper(),
                 bg=C["panel"], fg=C["white"],
                 font=("Consolas", 11, "bold"),
                 letter_spacing=3).pack(pady=(4, 0))
        tk.Label(logo_frame, text=f"v{APP_VERSION}",
                 bg=C["panel"], fg=C["dim"],
                 font=("Consolas", 8)).pack()

        # Step indicators
        self._steps = [
            ("welcome",   "01", "Welcome"),
            ("options",   "02", "Options"),
            ("install",   "03", "Installing"),
            ("done",      "04", "Complete"),
        ]
        self._step_labels = {}
        self._step_dots   = {}

        steps_frame = tk.Frame(sb, bg=C["panel"])
        steps_frame.place(x=0, y=95, width=260, height=300)

        for i, (key, num, label) in enumerate(self._steps):
            row = tk.Frame(steps_frame, bg=C["panel"], height=52)
            row.pack(fill="x")
            row.pack_propagate(False)

            # Connector line
            if i < len(self._steps) - 1:
                line = tk.Frame(steps_frame, bg=C["border"], height=1)
                line.pack(fill="x", padx=34)

            # Dot canvas
            dot_cv = tk.Canvas(row, width=24, height=24, bg=C["panel"],
                               highlightthickness=0)
            dot_cv.place(x=22, y=14)
            dot_cv.create_oval(0, 0, 23, 23, fill=C["border2"], outline="")
            dot_cv.create_text(12, 12, text=num, fill=C["dim"],
                               font=("Consolas", 7, "bold"))
            self._step_dots[key] = dot_cv

            name_lbl = tk.Label(row, text=label.upper(),
                                bg=C["panel"], fg=C["dim"],
                                font=("Consolas", 9))
            name_lbl.place(x=56, y=18)
            self._step_labels[key] = name_lbl

        # System info at bottom of sidebar
        self._sysinfo_lbl = tk.Label(sb,
            text=f"Windows {platform.version()[:10]}\n"
                 f"{platform.machine()}  •  {'Admin' if is_admin() else 'User'}",
            bg=C["panel"], fg=C["dim"],
            font=("Consolas", 8), justify="left")
        self._sysinfo_lbl.place(x=20, y=540)

        # Python status badge
        self._py_badge = tk.Label(sb, text="⏳ Checking Python...",
                                  bg=C["panel"], fg=C["amber"],
                                  font=("Consolas", 8))
        self._py_badge.place(x=20, y=580)

        # Drag handle on sidebar
        sb.bind("<ButtonPress-1>", self._on_drag_start)
        sb.bind("<B1-Motion>",     self._on_drag)

    def _draw_icon(self, cv, cx, cy, size):
        """Draw the teal circuit/bolt icon on a canvas."""
        s = size
        # Outer ring
        cv.create_oval(cx-s, cy-s, cx+s, cy+s,
                       outline=C["teal"], width=2)
        # Inner bolt shape
        pts = [
            cx,      cy - s*0.65,
            cx+s*0.4, cy - s*0.05,
            cx+s*0.18, cy - s*0.05,
            cx+s*0.18, cy + s*0.65,
            cx-s*0.18, cy + s*0.65,
            cx-s*0.18, cy - s*0.05,
            cx-s*0.4, cy - s*0.05,
        ]
        cv.create_polygon(pts, fill=C["teal"], outline="")

    # ── PAGES ──────────────────────────────────────────────
    def _build_pages(self):
        for name in ("welcome", "options", "install", "done"):
            f = tk.Frame(self._content, bg=C["bg"])
            f.place(x=0, y=45, width=637, height=573)
            self._pages[name] = f

        self._build_welcome()
        self._build_options()
        self._build_install()
        self._build_done()

    def _show_page(self, name):
        for k, f in self._pages.items():
            f.lower()
        self._pages[name].lift()
        self._current_page = name

        # Update sidebar step indicators
        order = [s[0] for s in self._steps]
        cur_idx = order.index(name) if name in order else -1
        for i, (key, num, label) in enumerate(self._steps):
            dot = self._step_dots[key]
            lbl = self._step_labels[key]
            if i < cur_idx:
                dot.delete("all")
                dot.create_oval(0, 0, 23, 23, fill=C["teal_dim"], outline="")
                dot.create_text(12, 12, text="✓", fill=C["bg"],
                                font=("Consolas", 8, "bold"))
                lbl.config(fg=C["teal_dim"])
            elif i == cur_idx:
                dot.delete("all")
                dot.create_oval(0, 0, 23, 23, fill=C["teal"], outline="")
                dot.create_text(12, 12, text=num, fill=C["bg"],
                                font=("Consolas", 7, "bold"))
                lbl.config(fg=C["white"])
            else:
                dot.delete("all")
                dot.create_oval(0, 0, 23, 23, fill=C["border2"], outline="")
                dot.create_text(12, 12, text=num, fill=C["dim"],
                                font=("Consolas", 7, "bold"))
                lbl.config(fg=C["dim"])

    # ── WELCOME PAGE ───────────────────────────────────────
    def _build_welcome(self):
        f = self._pages["welcome"]

        # Big title
        tk.Label(f, text="WELCOME",
                 bg=C["bg"], fg=C["teal"],
                 font=("Consolas", 28, "bold")).place(x=40, y=55)

        tk.Label(f, text=APP_NAME,
                 bg=C["bg"], fg=C["white"],
                 font=("Consolas", 15)).place(x=42, y=100)

        # Divider
        tk.Frame(f, bg=C["teal"], height=2).place(x=40, y=130, width=80)

        # Description
        desc = (
            "This installer will set up everything you need\n"
            "to run PC Optimizer Pro on your machine.\n\n"
            "What will be installed:\n"
        )
        tk.Label(f, text=desc,
                 bg=C["bg"], fg=C["grey"],
                 font=("Consolas", 10),
                 justify="left").place(x=40, y=148)

        # Feature list with teal bullets
        items = [
            ("Python 3.11",           "Runtime environment"),
            ("PyQt6",                 "UI framework"),
            ("liquidctl",             "Corsair AIO fan control"),
            ("openrgb-python",        "RGB lighting control"),
            ("psutil + pynvml",       "Hardware monitoring"),
            ("PC Optimizer Pro",      "from github.com/Londopy/pc-optimizer"),
        ]
        for i, (name, desc2) in enumerate(items):
            y = 258 + i * 38
            # Teal dot
            dot = tk.Canvas(f, width=8, height=8, bg=C["bg"],
                            highlightthickness=0)
            dot.place(x=40, y=y + 4)
            dot.create_oval(0, 0, 7, 7, fill=C["teal"], outline="")

            tk.Label(f, text=name,
                     bg=C["bg"], fg=C["white"],
                     font=("Consolas", 10, "bold")).place(x=58, y=y)
            tk.Label(f, text=desc2,
                     bg=C["bg"], fg=C["dim"],
                     font=("Consolas", 9)).place(x=58, y=y + 16)

        # Requirements note
        note_frame = tk.Frame(f, bg=C["card"],
                              highlightbackground=C["border"],
                              highlightthickness=1)
        note_frame.place(x=40, y=498, width=557, height=40)
        tk.Label(note_frame,
                 text="  ⚠  Requires Windows 10/11 and an internet connection. "
                      "Admin rights recommended.",
                 bg=C["card"], fg=C["amber"],
                 font=("Consolas", 9)).pack(side="left", padx=6, pady=8)

        # Next button
        self._btn_welcome_next = self._make_btn(
            f, "NEXT  →", self._go_options, primary=True)
        self._btn_welcome_next.place(x=447, y=520)

    # ── OPTIONS PAGE ───────────────────────────────────────
    def _build_options(self):
        f = self._pages["options"]

        tk.Label(f, text="INSTALL OPTIONS",
                 bg=C["bg"], fg=C["teal"],
                 font=("Consolas", 22, "bold")).place(x=40, y=55)
        tk.Frame(f, bg=C["teal"], height=2).place(x=40, y=95, width=80)

        # Install path
        tk.Label(f, text="INSTALL LOCATION",
                 bg=C["bg"], fg=C["dim"],
                 font=("Consolas", 9, "bold"),
                 letter_spacing=2).place(x=40, y=118)

        path_frame = tk.Frame(f, bg=C["card"],
                              highlightbackground=C["border"],
                              highlightthickness=1)
        path_frame.place(x=40, y=138, width=461, height=36)

        path_entry = tk.Entry(path_frame,
                              textvariable=self._install_dir,
                              bg=C["card"], fg=C["white"],
                              insertbackground=C["teal"],
                              font=("Consolas", 10),
                              relief="flat", bd=0,
                              highlightthickness=0)
        path_entry.pack(fill="both", padx=10, pady=6)

        browse_btn = self._make_btn(f, "Browse", self._browse_dir, primary=False, small=True)
        browse_btn.place(x=508, y=138)

        # Checkboxes
        options = [
            ("Create Desktop shortcut",       self._create_shortcut),
            ("Add Python to PATH",             self._add_path),
            ("Launch on Windows startup",      self._autostart),
        ]

        tk.Label(f, text="OPTIONS",
                 bg=C["bg"], fg=C["dim"],
                 font=("Consolas", 9, "bold")).place(x=40, y=200)

        for i, (label, var) in enumerate(options):
            y = 224 + i * 46
            row = tk.Frame(f, bg=C["card"],
                           highlightbackground=C["border"],
                           highlightthickness=1)
            row.place(x=40, y=y, width=517, height=36)

            cb_cv = tk.Canvas(row, width=18, height=18,
                              bg=C["card"], highlightthickness=0)
            cb_cv.pack(side="left", padx=(12, 8), pady=9)

            def draw_check(cv, checked):
                cv.delete("all")
                if checked:
                    cv.create_rectangle(0, 0, 17, 17, fill=C["teal"],
                                        outline=C["teal"])
                    cv.create_text(9, 9, text="✓", fill=C["bg"],
                                   font=("Consolas", 9, "bold"))
                else:
                    cv.create_rectangle(0, 0, 17, 17, fill=C["border2"],
                                        outline=C["border2"])

            draw_check(cb_cv, var.get())

            lbl = tk.Label(row, text=label,
                           bg=C["card"], fg=C["grey"],
                           font=("Consolas", 10))
            lbl.pack(side="left")

            def on_toggle(cv=cb_cv, v=var, draw=draw_check):
                v.set(not v.get())
                draw(cv, v.get())

            cb_cv.bind("<Button-1>", lambda e, fn=on_toggle: fn())
            lbl.bind("<Button-1>",   lambda e, fn=on_toggle: fn())
            row.bind("<Button-1>",   lambda e, fn=on_toggle: fn())

        # Disk space
        space_frame = tk.Frame(f, bg=C["card"],
                               highlightbackground=C["border2"],
                               highlightthickness=1)
        space_frame.place(x=40, y=388, width=517, height=60)

        try:
            import shutil as sh
            total, used, free = sh.disk_usage("C:\\")
            free_gb = free / (1024**3)
            space_text = f"Free disk space:  {free_gb:.1f} GB"
            space_color = C["green"] if free_gb > 2 else C["red"]
        except:
            space_text = "Disk space: unknown"
            space_color = C["grey"]

        tk.Label(space_frame, text="DISK SPACE",
                 bg=C["card"], fg=C["dim"],
                 font=("Consolas", 8, "bold")).place(x=14, y=8)
        tk.Label(space_frame, text=space_text,
                 bg=C["card"], fg=space_color,
                 font=("Consolas", 10)).place(x=14, y=28)
        tk.Label(space_frame, text="Required: ~500 MB",
                 bg=C["card"], fg=C["dim"],
                 font=("Consolas", 9)).place(x=300, y=28)

        # Buttons
        back_btn = self._make_btn(f, "← BACK", lambda: self._show_page("welcome"))
        back_btn.place(x=40, y=520)

        self._btn_install = self._make_btn(
            f, "INSTALL  →", self._start_install, primary=True)
        self._btn_install.place(x=447, y=520)

    # ── INSTALL PAGE ───────────────────────────────────────
    def _build_install(self):
        f = self._pages["install"]

        tk.Label(f, text="INSTALLING",
                 bg=C["bg"], fg=C["teal"],
                 font=("Consolas", 22, "bold")).place(x=40, y=55)
        tk.Frame(f, bg=C["teal"], height=2).place(x=40, y=95, width=80)

        # Current task label
        self._task_lbl = tk.Label(f, text="Preparing...",
                                  bg=C["bg"], fg=C["white"],
                                  font=("Consolas", 11),
                                  wraplength=540, justify="left")
        self._task_lbl.place(x=40, y=118)

        # Main progress bar (custom drawn)
        self._prog_canvas = tk.Canvas(f, width=557, height=12,
                                      bg=C["card"], highlightthickness=1,
                                      highlightbackground=C["border"])
        self._prog_canvas.place(x=40, y=155)
        self._prog_fill = self._prog_canvas.create_rectangle(
            0, 0, 0, 12, fill=C["teal"], outline="")

        self._prog_pct_lbl = tk.Label(f, text="0%",
                                      bg=C["bg"], fg=C["teal"],
                                      font=("Consolas", 9, "bold"))
        self._prog_pct_lbl.place(x=600, y=151)

        # Sub-progress (byte count)
        self._sub_lbl = tk.Label(f, text="",
                                 bg=C["bg"], fg=C["dim"],
                                 font=("Consolas", 9))
        self._sub_lbl.place(x=40, y=176)

        # Log area
        log_frame = tk.Frame(f, bg=C["card"],
                             highlightbackground=C["border"],
                             highlightthickness=1)
        log_frame.place(x=40, y=200, width=557, height=280)

        self._log_text = tk.Text(log_frame,
                                 bg=C["card"], fg=C["grey"],
                                 font=("Consolas", 9),
                                 relief="flat", bd=0,
                                 state="disabled",
                                 insertbackground=C["teal"],
                                 selectbackground=C["teal_dim"],
                                 wrap="word")
        self._log_text.pack(fill="both", expand=True, padx=6, pady=6)

        # Tag colours
        self._log_text.tag_config("ok",   foreground=C["green"])
        self._log_text.tag_config("err",  foreground=C["red"])
        self._log_text.tag_config("warn", foreground=C["amber"])
        self._log_text.tag_config("info", foreground=C["teal"])
        self._log_text.tag_config("dim",  foreground=C["dim"])

        # Cancel button (hidden after done)
        self._cancel_btn = self._make_btn(f, "Cancel", self._cancel_install)
        self._cancel_btn.place(x=40, y=505)

        self._install_status_lbl = tk.Label(f, text="",
                                            bg=C["bg"], fg=C["dim"],
                                            font=("Consolas", 9))
        self._install_status_lbl.place(x=140, y=509)

    # ── DONE PAGE ──────────────────────────────────────────
    def _build_done(self):
        f = self._pages["done"]

        # Big checkmark
        check_cv = tk.Canvas(f, width=80, height=80,
                             bg=C["bg"], highlightthickness=0)
        check_cv.place(x=40, y=50)
        check_cv.create_oval(0, 0, 79, 79, fill=C["teal"], outline="")
        check_cv.create_text(40, 40, text="✓",
                             fill=C["bg"], font=("Consolas", 36, "bold"))

        tk.Label(f, text="INSTALLATION COMPLETE",
                 bg=C["bg"], fg=C["white"],
                 font=("Consolas", 18, "bold")).place(x=136, y=68)

        tk.Frame(f, bg=C["teal"], height=2).place(x=40, y=148, width=80)

        self._done_detail = tk.Label(f,
            text="PC Optimizer Pro has been installed successfully.",
            bg=C["bg"], fg=C["grey"],
            font=("Consolas", 10),
            justify="left", wraplength=540)
        self._done_detail.place(x=40, y=162)

        # What was installed summary
        summary_frame = tk.Frame(f, bg=C["card"],
                                 highlightbackground=C["border"],
                                 highlightthickness=1)
        summary_frame.place(x=40, y=210, width=557, height=240)

        self._summary_text = tk.Text(summary_frame,
                                     bg=C["card"], fg=C["grey"],
                                     font=("Consolas", 9),
                                     relief="flat", bd=0,
                                     state="disabled")
        self._summary_text.pack(fill="both", expand=True, padx=10, pady=10)
        self._summary_text.tag_config("ok",   foreground=C["green"])
        self._summary_text.tag_config("info", foreground=C["teal"])
        self._summary_text.tag_config("dim",  foreground=C["dim"])

        launch_btn = self._make_btn(f, "▶  LAUNCH APP",
                                    self._launch_app, primary=True)
        launch_btn.place(x=306, y=476)

        close_btn = self._make_btn(f, "Close", self.destroy)
        close_btn.place(x=447, y=520)

        open_folder_btn = self._make_btn(f, "Open Folder",
                                         self._open_install_folder)
        open_folder_btn.place(x=40, y=520)

    # ── WIDGETS ────────────────────────────────────────────
    def _make_btn(self, parent, text, command, primary=False, small=False):
        w = 80 if small else 140
        h = 36
        bg   = C["teal"]      if primary else C["card"]
        fg   = C["bg"]        if primary else C["grey"]
        abg  = C["teal_dim"]  if primary else C["border2"]

        btn = tk.Label(parent, text=text, bg=bg, fg=fg,
                       font=("Consolas", 9, "bold" if primary else "normal"),
                       relief="flat", bd=0, cursor="hand2",
                       highlightbackground=C["border"] if not primary else bg,
                       highlightthickness=1 if not primary else 0,
                       width=w//8, height=2 if not small else 1,
                       padx=8, pady=4)
        btn.bind("<Button-1>",  lambda e: command())
        btn.bind("<Enter>",     lambda e: btn.config(bg=abg))
        btn.bind("<Leave>",     lambda e: btn.config(bg=bg))
        return btn

    # ── DRAG ───────────────────────────────────────────────
    def _on_drag_start(self, event):
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def _on_drag(self, event):
        self.geometry(f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}")

    def _minimize(self):
        self.overrideredirect(False)
        self.iconify()
        self.bind("<Map>", self._on_restore)

    def _on_restore(self, e):
        self.overrideredirect(True)
        self.unbind("<Map>")

    # ── ACTIONS ────────────────────────────────────────────
    def _browse_dir(self):
        from tkinter import filedialog
        d = filedialog.askdirectory(title="Choose install location",
                                    initialdir=self._install_dir.get())
        if d:
            self._install_dir.set(os.path.normpath(d))

    def _go_options(self):
        self._show_page("options")

    def _cancel_install(self):
        self._cancelled = True
        self._log("Installation cancelled by user.", "warn")

    def _check_python_async(self):
        def _check():
            exe = find_python()
            if exe:
                ver = get_python_version(exe)
                self._python_exe = exe
                self.after(0, lambda: self._py_badge.config(
                    text=f"✓ {ver}", fg=C["green"]))
            else:
                self.after(0, lambda: self._py_badge.config(
                    text="✗ Python not found", fg=C["amber"]))
        threading.Thread(target=_check, daemon=True).start()

    # ── INSTALL LOGIC ──────────────────────────────────────
    def _start_install(self):
        self._show_page("install")
        self._cancelled = False
        self._install_thread = threading.Thread(
            target=self._run_install, daemon=True)
        self._install_thread.start()

    def _log(self, msg, level="dim"):
        def _do():
            self._log_text.config(state="normal")
            self._log_text.insert("end", msg + "\n", level)
            self._log_text.see("end")
            self._log_text.config(state="disabled")
        self.after(0, _do)

    def _set_task(self, text):
        self.after(0, lambda: self._task_lbl.config(text=text))

    def _set_progress(self, pct):
        def _do():
            w = int(557 * pct / 100)
            self._prog_canvas.coords(self._prog_fill, 0, 0, w, 12)
            self._prog_pct_lbl.config(text=f"{int(pct)}%")
        self.after(0, _do)

    def _set_sub(self, text):
        self.after(0, lambda: self._sub_lbl.config(text=text))

    def _run_install(self):
        """Main installation sequence — runs in background thread."""
        summary_lines = []
        install_dir = self._install_dir.get()
        total_steps = 5
        step = 0

        try:
            # ── STEP 1: Python ──────────────────────────────
            step += 1
            self._set_task(f"[{step}/{total_steps}]  Checking Python installation...")
            self._set_progress(step / total_steps * 15)
            self._log("─" * 50, "dim")
            self._log(f"STEP {step}: Python Runtime", "info")

            exe = find_python()
            if exe:
                ver = get_python_version(exe)
                self._log(f"  ✓ Found: {ver}  ({exe})", "ok")
                self._python_exe = exe
                self.after(0, lambda v=ver: self._py_badge.config(
                    text=f"✓ {v}", fg=C["green"]))
                summary_lines.append(f"✓  Python  ({ver})")
            else:
                self._log(f"  ⬇  Python not found. Downloading Python {PYTHON_VERSION}...", "warn")
                self._set_task(f"[{step}/{total_steps}]  Downloading Python {PYTHON_VERSION}...")

                tmp_dir = os.environ.get("TEMP", "C:\\Temp")
                py_installer = os.path.join(tmp_dir, f"python-{PYTHON_VERSION}-amd64.exe")

                try:
                    download_with_progress(
                        PYTHON_URL, py_installer,
                        progress_cb=lambda p: self._set_progress(p * 0.12),
                        label_cb=self._set_sub
                    )
                    self._log(f"  ✓ Downloaded to {py_installer}", "ok")
                except Exception as e:
                    self._log(f"  ✗ Download failed: {e}", "err")
                    self._log("    Please install Python 3.11 manually from python.org", "warn")
                    summary_lines.append("✗  Python  (download failed — install manually)")
                    py_installer = None

                if py_installer and os.path.isfile(py_installer):
                    self._set_task(f"[{step}/{total_steps}]  Installing Python {PYTHON_VERSION}...")
                    self._log("  Running Python installer (silent)...", "dim")
                    self._set_sub("")

                    flags = "/quiet InstallAllUsers=0 PrependPath=1 Include_test=0"
                    if self._add_path.get():
                        flags += " PrependPath=1"
                    r = subprocess.run(
                        [py_installer] + flags.split(),
                        capture_output=True, timeout=180
                    )
                    if r.returncode in (0, 1602, 1603):
                        self._log(f"  ✓ Python {PYTHON_VERSION} installed", "ok")
                        summary_lines.append(f"✓  Python {PYTHON_VERSION}")
                        exe = find_python()
                        self._python_exe = exe
                    else:
                        self._log(f"  ✗ Installer returned code {r.returncode}", "err")
                        summary_lines.append("✗  Python  (install failed)")

            if self._cancelled:
                return
            self._set_sub("")
            self._set_progress(step / total_steps * 100 * 0.2)

            # ── STEP 2: pip upgrade ─────────────────────────
            step += 1
            self._set_task(f"[{step}/{total_steps}]  Upgrading pip...")
            self._log("─" * 50, "dim")
            self._log(f"STEP {step}: Package Manager", "info")

            if self._python_exe:
                r = subprocess.run(
                    [self._python_exe, "-m", "pip", "install",
                     "--upgrade", "pip", "--quiet"],
                    capture_output=True, text=True, timeout=60
                )
                self._log("  ✓ pip upgraded", "ok")
            else:
                self._log("  ✗ Python not available — skipping pip", "err")

            if self._cancelled:
                return
            self._set_progress(step / total_steps * 100 * 0.2)

            # ── STEP 3: Python packages ─────────────────────
            step += 1
            self._set_task(f"[{step}/{total_steps}]  Installing Python packages...")
            self._log("─" * 50, "dim")
            self._log(f"STEP {step}: Python Dependencies", "info")

            if self._python_exe:
                for i, (pkg_name, pkg_spec) in enumerate(PACKAGES):
                    if self._cancelled:
                        return
                    self._set_task(f"[{step}/{total_steps}]  Installing {pkg_name}...")
                    self._log(f"  ⬇  {pkg_name}...", "dim")
                    pct_start = 0.4 + (i / len(PACKAGES)) * 0.3
                    self._set_progress(pct_start * 100)

                    r = subprocess.run(
                        [self._python_exe, "-m", "pip", "install",
                         pkg_spec, "--quiet", "--no-warn-script-location"],
                        capture_output=True, text=True, timeout=120
                    )
                    if r.returncode == 0:
                        self._log(f"  ✓ {pkg_name}", "ok")
                        summary_lines.append(f"✓  {pkg_name}")
                    else:
                        err_short = (r.stderr or r.stdout or "").strip()[-120:]
                        self._log(f"  ✗ {pkg_name}: {err_short}", "err")
                        summary_lines.append(f"✗  {pkg_name}  (failed)")
            else:
                self._log("  ✗ Python not found — cannot install packages", "err")

            if self._cancelled:
                return
            self._set_progress(70)

            # ── STEP 4: Download from GitHub ────────────────
            step += 1
            self._set_task(f"[{step}/{total_steps}]  Downloading PC Optimizer Pro from GitHub...")
            self._log("─" * 50, "dim")
            self._log(f"STEP {step}: Downloading App", "info")
            self._log(f"  URL: {GITHUB_ZIP_URL}", "dim")

            tmp_dir = os.environ.get("TEMP", "C:\\Temp")
            zip_path = os.path.join(tmp_dir, "pc-optimizer.zip")

            try:
                download_with_progress(
                    GITHUB_ZIP_URL, zip_path,
                    progress_cb=lambda p: self._set_progress(70 + p * 0.15),
                    label_cb=self._set_sub
                )
                self._log(f"  ✓ Downloaded {os.path.getsize(zip_path) // 1024} KB", "ok")
                self._set_sub("")

                # Extract
                self._set_task(f"[{step}/{total_steps}]  Extracting files...")
                self._log(f"  Extracting to {install_dir}...", "dim")

                os.makedirs(install_dir, exist_ok=True)
                with zipfile.ZipFile(zip_path, "r") as z:
                    members = z.namelist()
                    prefix = members[0] if members[0].endswith("/") else ""
                    for member in members:
                        if self._cancelled:
                            return
                        rel = member[len(prefix):] if prefix else member
                        if not rel:
                            continue
                        dest_path = os.path.join(install_dir, rel)
                        if member.endswith("/"):
                            os.makedirs(dest_path, exist_ok=True)
                        else:
                            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                            with z.open(member) as src, open(dest_path, "wb") as dst:
                                dst.write(src.read())

                self._log(f"  ✓ Extracted to {install_dir}", "ok")
                summary_lines.append(f"✓  App files  ({install_dir})")

            except Exception as e:
                self._log(f"  ✗ Download/extract error: {e}", "err")
                summary_lines.append("✗  App files  (download failed)")

            self._set_progress(88)

            # ── STEP 5: Shortcuts & finish ──────────────────
            step += 1
            self._set_task(f"[{step}/{total_steps}]  Finalising installation...")
            self._log("─" * 50, "dim")
            self._log(f"STEP {step}: Shortcuts & Configuration", "info")

            # Find main.py
            main_py = os.path.join(install_dir, "src", "main.py")
            if not os.path.isfile(main_py):
                # Repo might have been extracted with subfolder
                for root, dirs, files in os.walk(install_dir):
                    if "main.py" in files and "src" in root:
                        main_py = os.path.join(root, "main.py")
                        break

            # Desktop shortcut
            if self._create_shortcut.get() and self._python_exe and os.path.isfile(main_py):
                try:
                    self._create_desktop_shortcut(main_py)
                    self._log("  ✓ Desktop shortcut created", "ok")
                    summary_lines.append("✓  Desktop shortcut")
                except Exception as e:
                    self._log(f"  ✗ Shortcut error: {e}", "err")

            # Autostart
            if self._autostart.get() and self._python_exe and os.path.isfile(main_py):
                try:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                        0, winreg.KEY_SET_VALUE)
                    winreg.SetValueEx(key, "PCOptimizerPro", 0, winreg.REG_SZ,
                        f'"{self._python_exe}" "{main_py}" --minimized')
                    winreg.CloseKey(key)
                    self._log("  ✓ Autostart entry added", "ok")
                    summary_lines.append("✓  Windows autostart")
                except Exception as e:
                    self._log(f"  ✗ Autostart: {e}", "err")

            self._set_progress(100)
            self._set_task("Installation complete!")
            self._log("─" * 50, "dim")
            self._log("✓  DONE!  PC Optimizer Pro is ready.", "ok")

        except Exception as e:
            self._log(f"\n✗  Unexpected error: {e}", "err")
            import traceback
            self._log(traceback.format_exc(), "err")

        # Transition to Done page
        self.after(800, lambda: self._finish_install(summary_lines, install_dir))

    def _finish_install(self, summary_lines, install_dir):
        self._show_page("done")

        # Populate summary
        self._summary_text.config(state="normal")
        self._summary_text.insert("end", "INSTALLATION SUMMARY\n", "info")
        self._summary_text.insert("end", "─" * 38 + "\n", "dim")
        self._summary_text.insert("end", f"Location:  {install_dir}\n\n", "dim")
        for line in summary_lines:
            tag = "ok" if line.startswith("✓") else "err"
            self._summary_text.insert("end", f"  {line}\n", tag)
        self._summary_text.insert("end", "\n─" * 19 + "\n", "dim")
        self._summary_text.insert("end",
            "To launch:  double-click the Desktop shortcut\n"
            "       or:  python src/main.py  in the install folder\n", "dim")
        self._summary_text.config(state="disabled")

        self._done_install_dir = install_dir

        # Find main.py
        self._done_main_py = None
        for root, dirs, files in os.walk(install_dir):
            if "main.py" in files and "src" in root:
                self._done_main_py = os.path.join(root, "main.py")
                break

    def _create_desktop_shortcut(self, main_py):
        """Create a .bat launcher as a Desktop shortcut (no pywin32 needed)."""
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        bat_path = os.path.join(desktop, f"{APP_NAME}.bat")
        with open(bat_path, "w") as f:
            f.write(f'@echo off\n"{self._python_exe}" "{main_py}"\n')
        # Try to create a proper .lnk if pywin32 is available
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(
                os.path.join(desktop, f"{APP_NAME}.lnk"))
            shortcut.Targetpath = self._python_exe
            shortcut.Arguments = f'"{main_py}"'
            shortcut.WorkingDirectory = os.path.dirname(main_py)
            shortcut.Description = APP_NAME
            shortcut.save()
            os.remove(bat_path)  # Remove bat if .lnk worked
        except ImportError:
            pass  # .bat launcher is fine

    def _launch_app(self):
        if self._done_main_py and self._python_exe:
            subprocess.Popen([self._python_exe, self._done_main_py],
                             cwd=os.path.dirname(self._done_main_py))
        else:
            messagebox.showinfo(APP_NAME,
                "Could not find main.py. Navigate to your install folder and run:\n"
                "  python src/main.py")

    def _open_install_folder(self):
        try:
            subprocess.Popen(["explorer", getattr(self, "_done_install_dir",
                                                   DEFAULT_INSTALL)])
        except:
            pass


# ══════════════════════════════════════════════════════════
#  BOOTSTRAP: if Python not found, show minimal fallback
# ══════════════════════════════════════════════════════════
def _minimal_fallback():
    """Shown if tkinter itself is broken (extremely rare)."""
    import subprocess
    msg = (
        f"PC Optimizer Pro Installer\n\n"
        f"Could not launch the graphical installer.\n\n"
        f"Please install Python 3.11+ from:\n"
        f"  https://www.python.org/downloads/\n\n"
        f"Then run:\n"
        f"  pip install PyQt6 psutil pynvml liquidctl openrgb-python\n\n"
        f"And download the app:\n"
        f"  https://github.com/{GITHUB_USER}/{GITHUB_REPO}"
    )
    try:
        ctypes.windll.user32.MessageBoxW(0, msg, f"{APP_NAME} Installer", 0x40)
    except:
        print(msg)


# ══════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════
if __name__ == "__main__":
    # On Windows, elevate if needed
    if sys.platform == "win32" and not is_admin():
        # Soft elevation — ask but don't hard-require
        try:
            elevate()
        except SystemExit:
            pass  # User declined — continue without admin

    try:
        app = InstallerApp()
        app.mainloop()
    except Exception as e:
        print(f"Installer error: {e}")
        import traceback
        traceback.print_exc()
        _minimal_fallback()
