"""
Dashboard Page - Live hardware metrics
CPU, GPU, RAM, temps, and quick-action buttons
"""
import os
import platform
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QProgressBar, QGridLayout, QPushButton,
    QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import pynvml
    pynvml.nvmlInit()
    HAS_NVML = True
except Exception:
    HAS_NVML = False


def card(parent=None):
    f = QFrame(parent)
    f.setObjectName("card")
    return f


class MetricCard(QFrame):
    def __init__(self, title, unit="", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        self.title_lbl = QLabel(title.upper())
        self.title_lbl.setObjectName("section_header")
        self.title_lbl.setStyleSheet("color: #484f58; font-size: 10px; letter-spacing: 1.5px;")
        layout.addWidget(self.title_lbl)

        val_row = QHBoxLayout()
        val_row.setSpacing(4)
        self.val_lbl = QLabel("--")
        self.val_lbl.setObjectName("metric_value")
        self.val_lbl.setStyleSheet("color: #ffffff; font-size: 32px; font-weight: bold; font-family: Consolas;")
        val_row.addWidget(self.val_lbl)

        if unit:
            u = QLabel(unit)
            u.setStyleSheet("color: #484f58; font-size: 13px; padding-top: 12px;")
            val_row.addWidget(u, alignment=Qt.AlignmentFlag.AlignBottom)
        val_row.addStretch()
        layout.addLayout(val_row)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        layout.addWidget(self.bar)

        self.sub_lbl = QLabel("")
        self.sub_lbl.setStyleSheet("color: #484f58; font-size: 11px;")
        layout.addWidget(self.sub_lbl)

    def update(self, value, sub="", bar_value=None, warn=False, danger=False):
        self.val_lbl.setText(str(value))
        self.sub_lbl.setText(sub)
        bv = bar_value if bar_value is not None else (int(value) if str(value).isdigit() else 0)
        self.bar.setValue(min(100, max(0, bv)))
        if danger:
            self.bar.setObjectName("danger")
            self.val_lbl.setStyleSheet("color: #f85149; font-size: 32px; font-weight: bold; font-family: Consolas;")
        elif warn:
            self.bar.setObjectName("warn")
            self.val_lbl.setStyleSheet("color: #e3b341; font-size: 32px; font-weight: bold; font-family: Consolas;")
        else:
            self.bar.setObjectName("")
            self.val_lbl.setStyleSheet("color: #00d4aa; font-size: 32px; font-weight: bold; font-family: Consolas;")
        self.bar.style().unpolish(self.bar)
        self.bar.style().polish(self.bar)


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

        self._timer = QTimer()
        self._timer.timeout.connect(self._refresh)
        self._timer.start(1500)

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # System info banner
        info_bar = QFrame()
        info_bar.setObjectName("card_accent")
        info_bar.setStyleSheet("QFrame#card_accent { background: #0d1117; border: 1px solid #00d4aa33; border-radius: 8px; }")
        info_layout = QHBoxLayout(info_bar)
        info_layout.setContentsMargins(20, 14, 20, 14)

        cpu_name = "Unknown CPU"
        try:
            import subprocess
            result = subprocess.run(["wmic", "cpu", "get", "name"], capture_output=True, text=True, timeout=3)
            lines = [l.strip() for l in result.stdout.splitlines() if l.strip() and l.strip() != "Name"]
            if lines:
                cpu_name = lines[0]
        except:
            if HAS_PSUTIL:
                cpu_name = f"{psutil.cpu_count(logical=False)} cores / {psutil.cpu_count()} threads"

        sys_lbl = QLabel(f"🖥  {cpu_name}")
        sys_lbl.setStyleSheet("color: #c9d1d9; font-size: 13px;")
        info_layout.addWidget(sys_lbl)

        info_layout.addStretch()

        os_lbl = QLabel(f"Windows  •  {platform.version()[:20]}")
        os_lbl.setStyleSheet("color: #484f58; font-size: 12px; font-family: Consolas;")
        info_layout.addWidget(os_lbl)

        layout.addWidget(info_bar)

        # Metrics grid
        section = QLabel("LIVE METRICS")
        section.setObjectName("section_header")
        layout.addWidget(section)

        grid = QGridLayout()
        grid.setSpacing(12)

        self.cpu_card = MetricCard("CPU Load", "%")
        self.ram_card = MetricCard("RAM Usage", "%")
        self.gpu_card = MetricCard("GPU Load", "%")
        self.vram_card = MetricCard("VRAM", "GB")
        self.cpu_temp_card = MetricCard("CPU Temp", "°C")
        self.gpu_temp_card = MetricCard("GPU Temp", "°C")

        cards = [self.cpu_card, self.ram_card, self.gpu_card,
                 self.vram_card, self.cpu_temp_card, self.gpu_temp_card]
        for i, c in enumerate(cards):
            grid.addWidget(c, i // 3, i % 3)

        layout.addLayout(grid)

        # Quick actions
        section2 = QLabel("QUICK ACTIONS")
        section2.setObjectName("section_header")
        layout.addWidget(section2)

        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)

        quick_actions = [
            ("⚡  Boost Now",   "#00d4aa", "#0a0e14", self._quick_boost),
            ("🗑  Clear RAM",    "#21262d", "#c9d1d9", self._clear_ram),
            ("❄  Fan: Auto",   "#21262d", "#c9d1d9", self._fan_auto),
            ("◉  Kill Bloat",  "#da363320", "#f85149", self._kill_bloat),
        ]
        for label, bg, fg, cb in quick_actions:
            btn = QPushButton(label)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg};
                    color: {fg};
                    border: 1px solid #30363d;
                    border-radius: 6px;
                    padding: 10px 18px;
                    font-size: 13px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ background-color: #21262d; color: #ffffff; }}
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(cb)
            actions_row.addWidget(btn)

        layout.addLayout(actions_row)

        # Process list (top CPU consumers)
        section3 = QLabel("TOP PROCESSES")
        section3.setObjectName("section_header")
        layout.addWidget(section3)

        self.proc_frame = QFrame()
        self.proc_frame.setObjectName("card")
        self.proc_layout = QVBoxLayout(self.proc_frame)
        self.proc_layout.setContentsMargins(16, 12, 16, 12)
        self.proc_layout.setSpacing(4)
        layout.addWidget(self.proc_frame)
        layout.addStretch()

    def _refresh(self):
        if not HAS_PSUTIL:
            return

        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory()
        ram_pct = ram.percent
        ram_used = ram.used / (1024**3)
        ram_total = ram.total / (1024**3)

        self.cpu_card.update(f"{cpu:.0f}", f"Cores: {psutil.cpu_count()}", int(cpu),
                             warn=cpu > 80, danger=cpu > 95)
        self.ram_card.update(f"{ram_pct:.0f}",
                             f"{ram_used:.1f} / {ram_total:.1f} GB",
                             int(ram_pct), warn=ram_pct > 80, danger=ram_pct > 90)

        if HAS_NVML:
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                gpu_util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                gpu_temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)

                self.gpu_card.update(f"{gpu_util.gpu}", f"RTX 3090 Ti", gpu_util.gpu,
                                     warn=gpu_util.gpu > 85)
                vram_used = gpu_mem.used / (1024**3)
                vram_total = gpu_mem.total / (1024**3)
                self.vram_card.update(f"{vram_used:.1f}",
                                      f"/ {vram_total:.0f} GB",
                                      int(vram_used / vram_total * 100))
                self.gpu_temp_card.update(f"{gpu_temp}", "°C",
                                           gpu_temp, warn=gpu_temp > 80, danger=gpu_temp > 90)
            except Exception:
                self.gpu_card.update("--", "NVML Error", 0)
        else:
            self.gpu_card.update("--", "pynvml not installed", 0)
            self.vram_card.update("--", "", 0)
            self.gpu_temp_card.update("--", "", 0)

        self.cpu_temp_card.update("--", "Install HardwareMonitor", 0)

        # Update process list
        self._refresh_processes()

    def _refresh_processes(self):
        while self.proc_layout.count():
            item = self.proc_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Header
        header = QWidget()
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        for text, stretch in [("Process", 4), ("PID", 1), ("CPU %", 1), ("RAM MB", 1)]:
            lbl = QLabel(text)
            lbl.setStyleSheet("color: #484f58; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
            h_layout.addWidget(lbl, stretch)
        self.proc_layout.addWidget(header)

        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background: #21262d;")
        self.proc_layout.addWidget(line)

        try:
            procs = []
            for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                try:
                    procs.append(p.info)
                except:
                    pass
            procs = sorted(procs, key=lambda x: x.get('cpu_percent') or 0, reverse=True)[:8]

            for p in procs:
                row = QWidget()
                r_layout = QHBoxLayout(row)
                r_layout.setContentsMargins(0, 2, 0, 2)
                name = (p.get('name') or 'unknown')[:32]
                pid = str(p.get('pid', ''))
                cpu_pct = f"{p.get('cpu_percent', 0):.1f}"
                mem_mb = f"{(p.get('memory_info').rss / (1024**2)):.0f}" if p.get('memory_info') else "--"

                cpu_f = float(cpu_pct)
                color = "#f85149" if cpu_f > 20 else "#e3b341" if cpu_f > 5 else "#8b949e"

                for text, stretch, clr in [(name, 4, "#c9d1d9"), (pid, 1, "#484f58"),
                                            (cpu_pct, 1, color), (mem_mb, 1, "#8b949e")]:
                    lbl = QLabel(text)
                    lbl.setStyleSheet(f"color: {clr}; font-size: 12px; font-family: Consolas;")
                    r_layout.addWidget(lbl, stretch)
                self.proc_layout.addWidget(row)
        except Exception as e:
            err = QLabel(f"Error: {e}")
            err.setStyleSheet("color: #484f58; font-size: 12px;")
            self.proc_layout.addWidget(err)

    def _quick_boost(self):
        import subprocess
        try:
            subprocess.run(["powercfg", "/s", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"],
                           capture_output=True)
        except:
            pass

    def _clear_ram(self):
        import ctypes
        ctypes.windll.psapi.EmptyWorkingSet(-1)

    def _fan_auto(self):
        pass

    def _kill_bloat(self):
        import subprocess
        for proc in ["OneDrive", "Teams", "YourPhone", "Cortana"]:
            subprocess.run(["taskkill", "/f", "/im", f"{proc}.exe"],
                           capture_output=True)
