"""
RGB / Lighting Page - OpenRGB Python client
Controls all RGB via OpenRGB SDK server
"""
import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QColorDialog, QSlider, QComboBox, QScrollArea,
    QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen

try:
    from openrgb import OpenRGBClient
    from openrgb.utils import RGBColor, DeviceType
    HAS_OPENRGB = True
except ImportError:
    HAS_OPENRGB = False


class ColorButton(QPushButton):
    """A button that shows its current color and opens a color picker."""
    colorChanged = pyqtSignal(QColor)

    def __init__(self, initial_color=QColor(0, 212, 170), parent=None):
        super().__init__(parent)
        self._color = initial_color
        self._update_style()
        self.setFixedSize(40, 40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self._pick_color)

    def _update_style(self):
        r, g, b = self._color.red(), self._color.green(), self._color.blue()
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgb({r},{g},{b});
                border: 2px solid #30363d;
                border-radius: 20px;
            }}
            QPushButton:hover {{ border-color: #00d4aa; }}
        """)

    def _pick_color(self):
        color = QColorDialog.getColor(self._color, self, "Pick Color")
        if color.isValid():
            self._color = color
            self._update_style()
            self.colorChanged.emit(color)

    def get_rgb(self):
        return self._color.red(), self._color.green(), self._color.blue()

    def set_color(self, qcolor):
        self._color = qcolor
        self._update_style()


class RGBPage(QWidget):
    def __init__(self):
        super().__init__()
        self._client = None
        self._devices = []
        self._build_ui()

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

        # Warning if no openrgb
        if not HAS_OPENRGB:
            warn = QFrame()
            warn.setStyleSheet("background: #e3b34120; border: 1px solid #e3b34160; border-radius: 8px;")
            warn_l = QHBoxLayout(warn)
            warn_l.setContentsMargins(16, 12, 16, 12)
            QLabel("⚠  openrgb-python not installed. Run: pip install openrgb-python", warn).setStyleSheet("color: #e3b341;")
            layout.addWidget(warn)

        # Connection
        section = QLabel("OPENRGB CONNECTION")
        section.setObjectName("section_header")
        layout.addWidget(section)

        conn_card = QFrame()
        conn_card.setObjectName("card")
        conn_l = QVBoxLayout(conn_card)
        conn_l.setContentsMargins(16, 14, 16, 16)
        conn_l.setSpacing(10)

        info = QLabel("OpenRGB must be running with SDK Server enabled (Settings → SDK Server, port 6742).\n"
                      "Launch OpenRGB.exe with --server flag for background operation.")
        info.setStyleSheet("color: #8b949e; font-size: 12px;")
        info.setWordWrap(True)
        conn_l.addWidget(info)

        row = QHBoxLayout()
        self.connect_btn = QPushButton("🔌  Connect to OpenRGB")
        self.connect_btn.setObjectName("primary_btn")
        self.connect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.connect_btn.clicked.connect(self._connect)
        row.addWidget(self.connect_btn)

        self.conn_status = QLabel("Not connected")
        self.conn_status.setStyleSheet("color: #484f58; font-size: 12px;")
        row.addWidget(self.conn_status)
        row.addStretch()
        conn_l.addLayout(row)
        layout.addWidget(conn_card)

        # Global color
        section2 = QLabel("GLOBAL COLOR")
        section2.setObjectName("section_header")
        layout.addWidget(section2)

        global_card = QFrame()
        global_card.setObjectName("card")
        global_l = QVBoxLayout(global_card)
        global_l.setContentsMargins(16, 14, 16, 16)
        global_l.setSpacing(12)

        color_row = QHBoxLayout()
        color_row.setSpacing(12)

        self.global_color_btn = ColorButton()
        color_row.addWidget(self.global_color_btn)

        color_lbl = QLabel("Pick a color to apply to all RGB devices at once")
        color_lbl.setStyleSheet("color: #8b949e; font-size: 13px;")
        color_row.addWidget(color_lbl)
        color_row.addStretch()

        apply_all_btn = QPushButton("Apply to All")
        apply_all_btn.setObjectName("primary_btn")
        apply_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_all_btn.clicked.connect(self._apply_global)
        color_row.addWidget(apply_all_btn)
        global_l.addLayout(color_row)

        # Quick colors
        quick_row = QHBoxLayout()
        quick_row.setSpacing(8)
        quick_colors = [
            ("Teal",    QColor(0, 212, 170)),
            ("Red",     QColor(248, 81, 73)),
            ("Blue",    QColor(0, 180, 216)),
            ("Purple",  QColor(168, 85, 247)),
            ("White",   QColor(255, 255, 255)),
            ("Off",     QColor(0, 0, 0)),
        ]
        for name, color in quick_colors:
            btn = ColorButton(color)
            btn.setToolTip(name)
            r, g, b = color.red(), color.green(), color.blue()
            btn.clicked.disconnect()
            btn.clicked.connect(lambda _, c=color: self._apply_color(c.red(), c.green(), c.blue()))
            quick_row.addWidget(btn)
        quick_row.addStretch()
        global_l.addLayout(quick_row)
        layout.addWidget(global_card)

        # Presets/effects
        section3 = QLabel("LIGHTING EFFECTS")
        section3.setObjectName("section_header")
        layout.addWidget(section3)

        effects_card = QFrame()
        effects_card.setObjectName("card")
        effects_l = QVBoxLayout(effects_card)
        effects_l.setContentsMargins(16, 14, 16, 16)
        effects_l.setSpacing(10)

        effects_grid = QGridLayout()
        effects_grid.setSpacing(10)

        effects = [
            ("Static", "Set a fixed color"),
            ("Breathing", "Slow fade in/out"),
            ("Rainbow", "Cycle all colors"),
            ("Off", "Disable all lighting"),
        ]
        for i, (name, desc) in enumerate(effects):
            btn = QPushButton(f"{name}\n{desc}")
            btn.setObjectName("secondary_btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(60)
            btn.clicked.connect(lambda _, n=name.lower(): self._apply_mode(n))
            effects_grid.addWidget(btn, 0, i)

        effects_l.addLayout(effects_grid)
        layout.addWidget(effects_card)

        # Per-device list
        section4 = QLabel("PER-DEVICE CONTROL")
        section4.setObjectName("section_header")
        layout.addWidget(section4)

        self.devices_frame = QFrame()
        self.devices_frame.setObjectName("card")
        self.devices_layout = QVBoxLayout(self.devices_frame)
        self.devices_layout.setContentsMargins(16, 12, 16, 12)

        no_dev = QLabel("Connect to OpenRGB to see devices")
        no_dev.setStyleSheet("color: #484f58; font-size: 13px;")
        self.devices_layout.addWidget(no_dev)
        layout.addWidget(self.devices_frame)
        layout.addStretch()

    def _connect(self):
        if not HAS_OPENRGB:
            self.conn_status.setText("openrgb-python not installed")
            return

        def _do_connect():
            try:
                self._client = OpenRGBClient()
                self._devices = self._client.devices
                count = len(self._devices)
                self.conn_status.setText(f"✓ Connected — {count} device{'s' if count != 1 else ''} found")
                self.conn_status.setStyleSheet("color: #3fb950; font-size: 12px;")
                self._populate_devices()
            except Exception as e:
                self.conn_status.setText(f"Connection failed: {e}")
                self.conn_status.setStyleSheet("color: #f85149; font-size: 12px;")

        threading.Thread(target=_do_connect, daemon=True).start()

    def _populate_devices(self):
        while self.devices_layout.count():
            item = self.devices_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._devices:
            lbl = QLabel("No devices found")
            lbl.setStyleSheet("color: #484f58;")
            self.devices_layout.addWidget(lbl)
            return

        for dev in self._devices:
            row = QFrame()
            row_l = QHBoxLayout(row)
            row_l.setContentsMargins(0, 6, 0, 6)

            dev_lbl = QLabel(dev.name)
            dev_lbl.setStyleSheet("color: #c9d1d9; font-size: 13px;")
            dev_lbl.setFixedWidth(200)
            row_l.addWidget(dev_lbl)

            type_lbl = QLabel(str(dev.type).split(".")[-1])
            type_lbl.setStyleSheet("color: #484f58; font-size: 11px;")
            row_l.addWidget(type_lbl)
            row_l.addStretch()

            col_btn = ColorButton()
            row_l.addWidget(col_btn)

            apply_btn = QPushButton("Apply")
            apply_btn.setObjectName("secondary_btn")
            apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            apply_btn.clicked.connect(lambda _, d=dev, b=col_btn: self._apply_to_device(d, b.get_rgb()))
            row_l.addWidget(apply_btn)

            self.devices_layout.addWidget(row)

    def _apply_color(self, r, g, b):
        self.global_color_btn.set_color(QColor(r, g, b))
        if self._client:
            try:
                self._client.set_color(RGBColor(r, g, b))
            except Exception:
                pass

    def _apply_global(self):
        r, g, b = self.global_color_btn.get_rgb()
        self._apply_color(r, g, b)

    def _apply_to_device(self, dev, rgb):
        if not self._client:
            return
        try:
            dev.set_color(RGBColor(*rgb))
        except Exception as e:
            print(f"RGB error: {e}")

    def _apply_mode(self, mode_name):
        if not self._client:
            return
        try:
            if mode_name == "off":
                self._client.set_color(RGBColor(0, 0, 0))
            elif mode_name == "breathing":
                for dev in self._devices:
                    try:
                        dev.set_mode("breathing")
                    except:
                        pass
            elif mode_name == "rainbow":
                for dev in self._devices:
                    try:
                        dev.set_mode("rainbow")
                    except:
                        pass
        except Exception as e:
            print(f"Mode error: {e}")
