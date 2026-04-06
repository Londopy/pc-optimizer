"""
Fan Control Page - Corsair AIO + GPU fan control via liquidctl
"""
import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QSlider, QComboBox, QGridLayout, QScrollArea,
    QGroupBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

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


PRESET_CURVES = {
    "Silent":      [(20, 20), (30, 25), (40, 35), (50, 50), (60, 70), (70, 90)],
    "Balanced":    [(20, 30), (30, 40), (40, 55), (50, 70), (60, 85), (70, 100)],
    "Performance": [(20, 40), (30, 55), (40, 70), (50, 85), (60, 95), (70, 100)],
    "Max":         [(20, 60), (30, 70), (40, 80), (50, 90), (60, 100), (70, 100)],
}


class SliderRow(QWidget):
    valueChanged = pyqtSignal(int)

    def __init__(self, label, min_val=0, max_val=100, default=50, unit="%", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        lbl = QLabel(label)
        lbl.setFixedWidth(100)
        lbl.setStyleSheet("color: #8b949e; font-size: 13px;")
        layout.addWidget(lbl)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(min_val, max_val)
        self.slider.setValue(default)
        layout.addWidget(self.slider)

        self.val_lbl = QLabel(f"{default}{unit}")
        self.val_lbl.setFixedWidth(50)
        self.val_lbl.setStyleSheet("color: #00d4aa; font-size: 13px; font-family: Consolas; font-weight: bold;")
        self.val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.val_lbl)

        self._unit = unit
        self.slider.valueChanged.connect(self._on_change)

    def _on_change(self, val):
        self.val_lbl.setText(f"{val}{self._unit}")
        self.valueChanged.emit(val)

    def value(self):
        return self.slider.value()


class FanCard(QFrame):
    def __init__(self, title, channel, device_ref, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.channel = channel
        self.device_ref = device_ref

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(12)

        # Title row
        title_row = QHBoxLayout()
        title_lbl = QLabel(title.upper())
        title_lbl.setStyleSheet("color: #484f58; font-size: 10px; font-weight: bold; letter-spacing: 1.5px;")
        title_row.addWidget(title_lbl)
        title_row.addStretch()

        self.rpm_lbl = QLabel("--- RPM")
        self.rpm_lbl.setStyleSheet("color: #00d4aa; font-size: 13px; font-family: Consolas; font-weight: bold;")
        title_row.addWidget(self.rpm_lbl)
        layout.addLayout(title_row)

        # Mode selector
        mode_row = QHBoxLayout()
        mode_lbl = QLabel("Mode:")
        mode_lbl.setStyleSheet("color: #8b949e; font-size: 13px;")
        mode_lbl.setFixedWidth(50)
        mode_row.addWidget(mode_lbl)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Fixed", "Profile", "Silent", "Balanced", "Performance", "Max"])
        self.mode_combo.currentTextChanged.connect(self._on_mode_change)
        mode_row.addWidget(self.mode_combo)
        mode_row.addStretch()
        layout.addLayout(mode_row)

        # Fixed speed slider
        self.fixed_slider = SliderRow("Fixed Speed", 20, 100, 60)
        self.fixed_slider.valueChanged.connect(self._apply_fixed)
        layout.addWidget(self.fixed_slider)

        # Apply button
        apply_btn = QPushButton("Apply")
        apply_btn.setObjectName("primary_btn")
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.clicked.connect(self._apply)
        layout.addWidget(apply_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _on_mode_change(self, mode):
        self.fixed_slider.setVisible(mode == "Fixed")

    def _apply_fixed(self, val):
        pass  # Real-time preview only

    def _apply(self):
        if self.device_ref[0] is None:
            return
        mode = self.mode_combo.currentText()
        dev = self.device_ref[0]
        try:
            with dev.connect():
                if mode == "Fixed":
                    dev.set_fixed_speed(self.channel, self.fixed_slider.value())
                elif mode in PRESET_CURVES:
                    dev.set_speed_profile(self.channel, PRESET_CURVES[mode])
        except Exception as e:
            print(f"Fan control error: {e}")

    def update_rpm(self, rpm):
        self.rpm_lbl.setText(f"{rpm} RPM")


class FanControlPage(QWidget):
    def __init__(self):
        super().__init__()
        self._devices = []
        self._active_device = [None]
        self._build_ui()
        self._scan_devices()

        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._refresh_status)
        self._status_timer.start(3000)

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

        # Warning banner
        if not HAS_LIQUIDCTL:
            warn = QFrame()
            warn.setStyleSheet("background: #e3b34120; border: 1px solid #e3b34160; border-radius: 8px; padding: 12px;")
            warn_layout = QHBoxLayout(warn)
            warn_lbl = QLabel("⚠  liquidctl not installed. Run: pip install liquidctl")
            warn_lbl.setStyleSheet("color: #e3b341; font-size: 13px;")
            warn_layout.addWidget(warn_lbl)
            layout.addWidget(warn)

        # Device selector
        device_row = QHBoxLayout()
        device_row.setSpacing(12)

        dev_lbl = QLabel("DEVICE:")
        dev_lbl.setObjectName("section_header")
        device_row.addWidget(dev_lbl)

        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(280)
        self.device_combo.addItem("Scanning...")
        device_row.addWidget(self.device_combo)

        scan_btn = QPushButton("🔍  Rescan")
        scan_btn.setObjectName("secondary_btn")
        scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        scan_btn.clicked.connect(self._scan_devices)
        device_row.addWidget(scan_btn)

        device_row.addStretch()
        layout.addLayout(device_row)

        # Status cards
        status_row = QHBoxLayout()
        status_row.setSpacing(12)

        self._stat_cards = {}
        for label in ["Liquid Temp", "Fan RPM", "Pump RPM", "Pump Mode"]:
            card = QFrame()
            card.setObjectName("card")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(14, 12, 14, 12)
            cl.setSpacing(4)
            title = QLabel(label.upper())
            title.setStyleSheet("color: #484f58; font-size: 10px; font-weight: bold; letter-spacing: 1.5px;")
            val = QLabel("---")
            val.setStyleSheet("color: #00d4aa; font-size: 22px; font-weight: bold; font-family: Consolas;")
            cl.addWidget(title)
            cl.addWidget(val)
            status_row.addWidget(card)
            self._stat_cards[label] = val

        layout.addLayout(status_row)

        # Fan channel cards
        chan_grid = QGridLayout()
        chan_grid.setSpacing(12)

        self.fan1_card = FanCard("AIO Fan", "fan", self._active_device)
        self.pump_card = FanCard("Pump", "pump", self._active_device)
        chan_grid.addWidget(self.fan1_card, 0, 0)
        chan_grid.addWidget(self.pump_card, 0, 1)

        layout.addLayout(chan_grid)

        # GPU fan section
        gpu_header = QLabel("GPU FAN CONTROL")
        gpu_header.setObjectName("section_header")
        layout.addWidget(gpu_header)

        gpu_card = QFrame()
        gpu_card.setObjectName("card")
        gpu_cl = QVBoxLayout(gpu_card)
        gpu_cl.setContentsMargins(16, 14, 16, 16)
        gpu_cl.setSpacing(12)

        self.gpu_fan_slider = SliderRow("GPU Fan %", 30, 100, 70)
        gpu_cl.addWidget(self.gpu_fan_slider)

        gpu_note = QLabel("Note: GPU fan curves require NVIDIA Fan Control or MSI Afterburner API. "
                         "This slider targets pynvml fan lock (requires per-GPU support).")
        gpu_note.setStyleSheet("color: #484f58; font-size: 11px;")
        gpu_note.setWordWrap(True)
        gpu_cl.addWidget(gpu_note)

        gpu_apply = QPushButton("Apply GPU Fan")
        gpu_apply.setObjectName("primary_btn")
        gpu_apply.setCursor(Qt.CursorShape.PointingHandCursor)
        gpu_apply.clicked.connect(self._apply_gpu_fan)
        gpu_cl.addWidget(gpu_apply, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addWidget(gpu_card)

        # Quick presets
        presets_header = QLabel("QUICK PRESETS")
        presets_header.setObjectName("section_header")
        layout.addWidget(presets_header)

        presets_row = QHBoxLayout()
        presets_row.setSpacing(10)
        for name in ["Silent", "Balanced", "Performance", "Max"]:
            btn = QPushButton(name)
            btn.setObjectName("secondary_btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, n=name: self._apply_preset(n))
            presets_row.addWidget(btn)
        presets_row.addStretch()
        layout.addLayout(presets_row)
        layout.addStretch()

    def _scan_devices(self):
        def _scan():
            self.device_combo.clear()
            if not HAS_LIQUIDCTL:
                self.device_combo.addItem("liquidctl not installed")
                return
            try:
                devs = list(find_liquidctl_devices())
                self._devices = devs
                if devs:
                    for d in devs:
                        self.device_combo.addItem(str(d.description))
                    self._active_device[0] = devs[0]
                else:
                    self.device_combo.addItem("No liquidctl devices found")
            except Exception as e:
                self.device_combo.addItem(f"Scan error: {e}")

        threading.Thread(target=_scan, daemon=True).start()

    def _refresh_status(self):
        if not HAS_LIQUIDCTL or self._active_device[0] is None:
            return

        def _read():
            try:
                dev = self._active_device[0]
                with dev.connect():
                    status = dev.get_status()
                    status_dict = {k: v for k, v, *_ in status}
                    for label, key in [
                        ("Liquid Temp", "Liquid temperature"),
                        ("Fan RPM", "Fan 1 speed"),
                        ("Pump RPM", "Pump speed"),
                        ("Pump Mode", "Pump mode"),
                    ]:
                        val = status_dict.get(key, "---")
                        if label in self._stat_cards:
                            self._stat_cards[label].setText(str(val))
            except Exception:
                pass

        threading.Thread(target=_read, daemon=True).start()

    def _apply_gpu_fan(self):
        if not HAS_NVML:
            return
        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            pynvml.nvmlDeviceSetDefaultFanSpeed_v2(handle, 0)
        except Exception:
            pass

    def _apply_preset(self, preset):
        if self._active_device[0] is None:
            return
        curves = PRESET_CURVES.get(preset)
        if not curves:
            return

        def _apply():
            try:
                with self._active_device[0].connect():
                    self._active_device[0].set_speed_profile("fan", curves)
            except Exception as e:
                print(f"Preset error: {e}")

        threading.Thread(target=_apply, daemon=True).start()
