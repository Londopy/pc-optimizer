"""
Fan Control Page - Corsair AIO + Lian Li UNI FAN support via liquidctl
Supports: Corsair H-series AIOs, Lian Li UNI FAN SL/AL/SL-INF/SLV2/ALV2
"""
import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QSlider, QComboBox, QScrollArea,
    QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

try:
    from liquidctl import find_liquidctl_devices
    HAS_LIQUIDCTL = True
except ImportError:
    HAS_LIQUIDCTL = False

try:
    import pynvml
    pynvml.nvmlInit()
    HAS_NVML = True
except Exception:
    HAS_NVML = False

CORSAIR_KEYWORDS = ["corsair", "hydro", "commander", "capellix"]
LIANLI_KEYWORDS  = ["lian li", "lianli", "uni fan", "uni hub", "unifan", "ga ii"]

def classify_device(dev):
    name = (getattr(dev, 'description', '') or str(dev)).lower()
    if any(k in name for k in LIANLI_KEYWORDS):
        return "lianli"
    if any(k in name for k in CORSAIR_KEYWORDS):
        return "corsair"
    return "generic"

PRESET_CURVES = {
    "Silent":      [(20, 20), (30, 25), (40, 35), (50, 50), (60, 70), (70, 90)],
    "Balanced":    [(20, 30), (30, 40), (40, 55), (50, 70), (60, 85), (70, 100)],
    "Performance": [(20, 40), (30, 55), (40, 70), (50, 85), (60, 95), (70, 100)],
    "Max":         [(20, 60), (30, 70), (40, 80), (50, 90), (60, 100), (70, 100)],
}

LIANLI_CHANNELS = ["fan1", "fan2", "fan3", "fan4"]
LIANLI_PRESETS  = {"Silent": 25, "Balanced": 50, "Performance": 75, "Max": 100}


class SliderRow(QWidget):
    valueChanged = pyqtSignal(int)

    def __init__(self, label, min_val=0, max_val=100, default=50,
                 unit="%", label_width=110, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        if label:
            lbl = QLabel(label)
            lbl.setFixedWidth(label_width)
            lbl.setStyleSheet("color: #8b949e; font-size: 13px;")
            layout.addWidget(lbl)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(min_val, max_val)
        self.slider.setValue(default)
        layout.addWidget(self.slider)

        self.val_lbl = QLabel(f"{default}{unit}")
        self.val_lbl.setFixedWidth(52)
        self.val_lbl.setStyleSheet(
            "color: #00d4aa; font-size: 13px; font-family: Consolas; font-weight: bold;")
        self.val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.val_lbl)

        self._unit = unit
        self.slider.valueChanged.connect(self._on_change)

    def _on_change(self, val):
        self.val_lbl.setText(f"{val}{self._unit}")
        self.valueChanged.emit(val)

    def value(self):
        return self.slider.value()

    def setValue(self, v):
        self.slider.setValue(v)


def _section(text):
    l = QLabel(text)
    l.setStyleSheet("color: #484f58; font-size: 10px; font-weight: bold; letter-spacing: 1.5px;")
    return l

def _card():
    f = QFrame()
    f.setObjectName("card")
    return f


# ── Corsair AIO panel ─────────────────────────────────────
class CorsairPanel(QWidget):
    def __init__(self, device_ref, parent=None):
        super().__init__(parent)
        self.device_ref = device_ref
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # Status cards
        stat_row = QHBoxLayout()
        stat_row.setSpacing(12)
        self._stats = {}
        for lbl in ["Liquid Temp", "Fan RPM", "Pump RPM", "Pump Mode"]:
            c = _card()
            cl = QVBoxLayout(c)
            cl.setContentsMargins(14, 10, 14, 10)
            cl.setSpacing(3)
            t = QLabel(lbl.upper())
            t.setStyleSheet("color: #484f58; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
            v = QLabel("---")
            v.setStyleSheet("color: #00d4aa; font-size: 20px; font-weight: bold; font-family: Consolas;")
            cl.addWidget(t)
            cl.addWidget(v)
            stat_row.addWidget(c)
            self._stats[lbl] = v
        layout.addLayout(stat_row)

        # Controls grid
        grid = QGridLayout()
        grid.setSpacing(12)

        # Fan card
        fan_c = _card()
        fl = QVBoxLayout(fan_c)
        fl.setContentsMargins(16, 14, 16, 16)
        fl.setSpacing(12)
        fl.addWidget(_section("AIO FAN"))
        mode_row = QHBoxLayout()
        mode_lbl = QLabel("Mode:")
        mode_lbl.setStyleSheet("color: #8b949e; font-size: 13px;")
        mode_row.addWidget(mode_lbl)
        self._fan_mode = QComboBox()
        self._fan_mode.addItems(["Fixed", "Silent", "Balanced", "Performance", "Max"])
        self._fan_mode.currentTextChanged.connect(lambda m: self._fan_slider.setVisible(m == "Fixed"))
        mode_row.addWidget(self._fan_mode)
        mode_row.addStretch()
        fl.addLayout(mode_row)
        self._fan_slider = SliderRow("Speed", 20, 100, 60)
        fl.addWidget(self._fan_slider)
        grid.addWidget(fan_c, 0, 0)

        # Pump card
        pump_c = _card()
        pl = QVBoxLayout(pump_c)
        pl.setContentsMargins(16, 14, 16, 16)
        pl.setSpacing(12)
        pl.addWidget(_section("PUMP"))
        pm_row = QHBoxLayout()
        pm_lbl = QLabel("Pump Mode:")
        pm_lbl.setStyleSheet("color: #8b949e; font-size: 13px;")
        pm_row.addWidget(pm_lbl)
        self._pump_mode = QComboBox()
        self._pump_mode.addItems(["quiet", "balanced", "extreme"])
        self._pump_mode.setCurrentText("balanced")
        pm_row.addWidget(self._pump_mode)
        pm_row.addStretch()
        pl.addLayout(pm_row)
        self._pump_slider = SliderRow("Speed", 60, 100, 85)
        pl.addWidget(self._pump_slider)
        grid.addWidget(pump_c, 0, 1)

        layout.addLayout(grid)

        apply_btn = QPushButton("Apply Corsair Settings")
        apply_btn.setObjectName("primary_btn")
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.clicked.connect(self._apply)
        layout.addWidget(apply_btn, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addStretch()

    def _apply(self):
        dev = self.device_ref[0]
        if not dev: return
        mode = self._fan_mode.currentText()
        pump_mode = self._pump_mode.currentText()
        def _do():
            try:
                with dev.connect():
                    dev.initialize(pump_mode=pump_mode)
                    if mode == "Fixed":
                        dev.set_fixed_speed("fan", self._fan_slider.value())
                        dev.set_fixed_speed("pump", self._pump_slider.value())
                    elif mode in PRESET_CURVES:
                        dev.set_speed_profile("fan", PRESET_CURVES[mode])
            except Exception as e:
                print(f"Corsair error: {e}")
        threading.Thread(target=_do, daemon=True).start()

    def refresh_status(self):
        dev = self.device_ref[0]
        if not dev: return
        def _read():
            try:
                with dev.connect():
                    s = {k: v for k, v, *_ in dev.get_status()}
                    mapping = {
                        "Liquid temperature": "Liquid Temp",
                        "Fan 1 speed":        "Fan RPM",
                        "Pump speed":         "Pump RPM",
                        "Pump mode":          "Pump Mode",
                    }
                    for key, lbl in mapping.items():
                        if lbl in self._stats:
                            self._stats[lbl].setText(str(s.get(key, "---")))
            except Exception: pass
        threading.Thread(target=_read, daemon=True).start()


# ── Lian Li UNI FAN panel ─────────────────────────────────
class LianLiPanel(QWidget):
    def __init__(self, device_ref, parent=None):
        super().__init__(parent)
        self.device_ref = device_ref
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # Info banner
        info = QFrame()
        info.setStyleSheet("QFrame{background:#00d4aa11;border:1px solid #00d4aa33;border-radius:6px;}")
        il = QHBoxLayout(info)
        il.setContentsMargins(14, 9, 14, 9)
        info_lbl = QLabel(
            "ℹ  Lian Li UNI FAN SL / AL / SL-Infinity / SL V2 / AL V2  —  "
            "liquidctl 1.16.0+ required.  Close L-Connect 3 before using.")
        info_lbl.setStyleSheet("color: #00d4aa; font-size: 11px;")
        info_lbl.setWordWrap(True)
        il.addWidget(info_lbl)
        layout.addWidget(info)

        # RPM status cards
        rpm_row = QHBoxLayout()
        rpm_row.setSpacing(12)
        self._rpm_widgets = {}
        for i in range(1, 5):
            c = _card()
            cl = QVBoxLayout(c)
            cl.setContentsMargins(14, 10, 14, 10)
            cl.setSpacing(3)
            t = QLabel(f"PORT {i} RPM")
            t.setStyleSheet("color: #484f58; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
            v = QLabel("---")
            v.setStyleSheet("color: #00d4aa; font-size: 20px; font-weight: bold; font-family: Consolas;")
            cl.addWidget(t)
            cl.addWidget(v)
            rpm_row.addWidget(c)
            self._rpm_widgets[f"fan{i}"] = v
        layout.addLayout(rpm_row)

        # Per-channel sliders
        ch_card = _card()
        ch_l = QVBoxLayout(ch_card)
        ch_l.setContentsMargins(16, 14, 16, 16)
        ch_l.setSpacing(10)
        ch_l.addWidget(_section("PER-PORT SPEED  (UNI HUB ports 1 – 4)"))

        self._ch_sliders = {}
        for i, ch in enumerate(LIANLI_CHANNELS):
            row = QHBoxLayout()
            row.setSpacing(10)

            port_lbl = QLabel(f"Port {i+1}")
            port_lbl.setFixedWidth(48)
            port_lbl.setStyleSheet("color: #c9d1d9; font-size: 12px; font-weight: bold;")
            row.addWidget(port_lbl)

            slider = SliderRow("", 0, 100, 60, label_width=0)
            row.addWidget(slider)

            set_btn = QPushButton("Set")
            set_btn.setObjectName("secondary_btn")
            set_btn.setFixedWidth(48)
            set_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            set_btn.clicked.connect(lambda _, c=ch, s=slider: self._apply_channel(c, s.value()))
            row.addWidget(set_btn)

            ch_l.addLayout(row)
            self._ch_sliders[ch] = slider

        layout.addWidget(ch_card)

        # Global / preset controls
        global_card = _card()
        gl = QVBoxLayout(global_card)
        gl.setContentsMargins(16, 14, 16, 16)
        gl.setSpacing(12)
        gl.addWidget(_section("GLOBAL  (all ports at once)"))

        self._global_slider = SliderRow("All Ports", 0, 100, 60)
        gl.addWidget(self._global_slider)

        # Presets row
        p_row = QHBoxLayout()
        p_row.setSpacing(8)
        p_lbl = QLabel("Preset:")
        p_lbl.setStyleSheet("color: #8b949e; font-size: 13px;")
        p_row.addWidget(p_lbl)
        for name, duty in LIANLI_PRESETS.items():
            btn = QPushButton(name)
            btn.setObjectName("secondary_btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, d=duty: self._apply_preset(d))
            p_row.addWidget(btn)
        p_row.addStretch()
        gl.addLayout(p_row)

        apply_all_btn = QPushButton("Apply to All Ports")
        apply_all_btn.setObjectName("primary_btn")
        apply_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_all_btn.clicked.connect(self._apply_all)
        gl.addWidget(apply_all_btn, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addWidget(global_card)

        note = QLabel(
            "Lian Li UNI FAN uses fixed duty-cycle control via liquidctl. "
            "Temperature-based curves require L-Connect 3 or CoolerControl.")
        note.setStyleSheet("color: #484f58; font-size: 11px;")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch()

    def _apply_channel(self, channel, duty):
        dev = self.device_ref[0]
        if not dev: return
        def _do():
            try:
                with dev.connect():
                    dev.initialize()
                    dev.set_fixed_speed(channel, duty)
            except Exception as e:
                print(f"Lian Li channel {channel} error: {e}")
        threading.Thread(target=_do, daemon=True).start()

    def _apply_all(self):
        duty = self._global_slider.value()
        dev = self.device_ref[0]
        if not dev: return
        def _do():
            try:
                with dev.connect():
                    dev.initialize()
                    for ch in LIANLI_CHANNELS:
                        try:
                            dev.set_fixed_speed(ch, duty)
                        except Exception: pass
            except Exception as e:
                print(f"Lian Li apply all error: {e}")
        threading.Thread(target=_do, daemon=True).start()

    def _apply_preset(self, duty):
        self._global_slider.setValue(duty)
        for s in self._ch_sliders.values():
            s.setValue(duty)
        self._apply_all()

    def refresh_status(self):
        dev = self.device_ref[0]
        if not dev: return
        def _read():
            try:
                with dev.connect():
                    s = {k: v for k, v, *_ in dev.get_status()}
                    for i in range(1, 5):
                        key = f"Fan {i} speed"
                        alt = f"Fan speed {i}"
                        val = s.get(key, s.get(alt, "---"))
                        ch = f"fan{i}"
                        if ch in self._rpm_widgets:
                            self._rpm_widgets[ch].setText(str(val))
            except Exception: pass
        threading.Thread(target=_read, daemon=True).start()


# ══════════════════════════════════════════════════════════
#  MAIN PAGE
# ══════════════════════════════════════════════════════════
class FanControlPage(QWidget):
    def __init__(self):
        super().__init__()
        self._devices = []
        self._active_device = [None]
        self._active_type = "generic"
        self._build_ui()
        self._scan_devices()

        self._timer = QTimer()
        self._timer.timeout.connect(self._refresh_status)
        self._timer.start(3000)

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea{border:none;background:transparent;}")

        container = QWidget()
        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # liquidctl missing warning
        if not HAS_LIQUIDCTL:
            warn = QFrame()
            warn.setStyleSheet("background:#e3b34120;border:1px solid #e3b34160;border-radius:8px;")
            wl = QHBoxLayout(warn)
            wl.setContentsMargins(14, 10, 14, 10)
            QLabel("⚠  liquidctl not installed — run: pip install liquidctl",
                   warn).setStyleSheet("color:#e3b341;font-size:13px;")
            layout.addWidget(warn)

        # Device row
        dev_row = QHBoxLayout()
        dev_row.setSpacing(12)
        dev_row.addWidget(_section("DEVICE"))

        self._device_combo = QComboBox()
        self._device_combo.setMinimumWidth(340)
        self._device_combo.addItem("Scanning for devices...")
        self._device_combo.currentIndexChanged.connect(self._on_device_changed)
        dev_row.addWidget(self._device_combo)

        self._type_badge = QLabel("")
        self._type_badge.setStyleSheet(
            "color:#00d4aa;font-size:11px;font-weight:bold;"
            "background:#00d4aa22;border:1px solid #00d4aa44;"
            "border-radius:4px;padding:3px 8px;")
        dev_row.addWidget(self._type_badge)

        scan_btn = QPushButton("🔍  Rescan")
        scan_btn.setObjectName("secondary_btn")
        scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        scan_btn.clicked.connect(self._scan_devices)
        dev_row.addWidget(scan_btn)
        dev_row.addStretch()
        layout.addLayout(dev_row)

        # Panels (shown/hidden based on device type)
        self._corsair_panel = CorsairPanel(self._active_device)
        self._lianli_panel  = LianLiPanel(self._active_device)
        layout.addWidget(self._corsair_panel)
        layout.addWidget(self._lianli_panel)
        self._corsair_panel.hide()
        self._lianli_panel.hide()

        # GPU fan (always visible)
        layout.addWidget(self._build_gpu_section())
        layout.addStretch()

    def _build_gpu_section(self):
        card = _card()
        gl = QVBoxLayout(card)
        gl.setContentsMargins(16, 14, 16, 16)
        gl.setSpacing(12)
        gl.addWidget(_section("GPU FAN  (NVIDIA — pynvml)"))
        self._gpu_slider = SliderRow("GPU Fan %", 30, 100, 70)
        gl.addWidget(self._gpu_slider)
        note = QLabel(
            "Direct GPU fan lock requires pynvml and per-GPU NVML support. "
            "Use MSI Afterburner for full temperature-based curves.")
        note.setStyleSheet("color:#484f58;font-size:11px;")
        note.setWordWrap(True)
        gl.addWidget(note)
        apply_btn = QPushButton("Apply GPU Fan Speed")
        apply_btn.setObjectName("primary_btn")
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.clicked.connect(self._apply_gpu_fan)
        gl.addWidget(apply_btn, alignment=Qt.AlignmentFlag.AlignRight)
        return card

    def _scan_devices(self):
        def _scan():
            self._device_combo.clear()
            self._device_combo.addItem("Scanning...")
            if not HAS_LIQUIDCTL:
                self._device_combo.clear()
                self._device_combo.addItem("liquidctl not installed")
                return
            try:
                devs = list(find_liquidctl_devices())
                self._devices = devs
                self._device_combo.clear()
                if devs:
                    for d in devs:
                        desc = getattr(d, 'description', str(d))
                        dtype = classify_device(d)
                        tag = " [Lian Li]" if dtype == "lianli" else \
                              " [Corsair]" if dtype == "corsair" else " [Generic]"
                        self._device_combo.addItem(f"{desc}{tag}")
                    self._active_device[0] = devs[0]
                    self._active_type = classify_device(devs[0])
                    self._update_panel()
                else:
                    self._device_combo.addItem("No liquidctl devices found")
                    self._corsair_panel.hide()
                    self._lianli_panel.hide()
            except Exception as e:
                self._device_combo.clear()
                self._device_combo.addItem(f"Scan error: {e}")
        threading.Thread(target=_scan, daemon=True).start()

    def _on_device_changed(self, idx):
        if 0 <= idx < len(self._devices):
            self._active_device[0] = self._devices[idx]
            self._active_type = classify_device(self._devices[idx])
            self._update_panel()

    def _update_panel(self):
        self._corsair_panel.hide()
        self._lianli_panel.hide()
        if self._active_type == "lianli":
            self._lianli_panel.show()
            self._type_badge.setText("Lian Li UNI FAN")
            self._type_badge.setStyleSheet(
                "color:#e3b341;font-size:11px;font-weight:bold;"
                "background:#e3b34122;border:1px solid #e3b34144;"
                "border-radius:4px;padding:3px 8px;")
        else:
            self._corsair_panel.show()
            self._type_badge.setText("Corsair AIO" if self._active_type == "corsair" else "Generic")
            self._type_badge.setStyleSheet(
                "color:#00d4aa;font-size:11px;font-weight:bold;"
                "background:#00d4aa22;border:1px solid #00d4aa44;"
                "border-radius:4px;padding:3px 8px;")

    def _refresh_status(self):
        if self._active_type == "lianli":
            self._lianli_panel.refresh_status()
        else:
            self._corsair_panel.refresh_status()

    def _apply_gpu_fan(self):
        if not HAS_NVML: return
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            pynvml.nvmlDeviceSetDefaultFanSpeed_v2(handle, 0)
        except Exception as e:
            print(f"GPU fan error: {e}")
