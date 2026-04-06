"""
RGB / Lighting Page
Requires OpenRGB running with SDK server enabled.
Clearly explains setup requirements.
"""
import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QColorDialog, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

try:
    from openrgb import OpenRGBClient
    from openrgb.utils import RGBColor, DeviceType
    HAS_OPENRGB = True
except ImportError:
    HAS_OPENRGB = False


class ColorButton(QPushButton):
    def __init__(self, initial_color=QColor(0, 212, 170), parent=None):
        super().__init__(parent)
        self._color = initial_color
        self._update_style()
        self.setFixedSize(40, 40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self._pick)

    def _update_style(self):
        r, g, b = self._color.red(), self._color.green(), self._color.blue()
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgb({r},{g},{b});
                border: 2px solid #30363d; border-radius: 20px;
            }}
            QPushButton:hover {{ border-color: #00d4aa; }}
        """)

    def _pick(self):
        color = QColorDialog.getColor(self._color, self, "Pick Color")
        if color.isValid():
            self._color = color
            self._update_style()

    def get_rgb(self):
        return self._color.red(), self._color.green(), self._color.blue()

    def set_color(self, qcolor):
        self._color = qcolor
        self._update_style()


def _card():
    f = QFrame()
    f.setObjectName("card")
    return f

def _section(text):
    l = QLabel(text)
    l.setStyleSheet("color:#484f58;font-size:10px;font-weight:bold;letter-spacing:1.5px;")
    return l


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

        container = QWidget()
        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Missing package warning
        if not HAS_OPENRGB:
            warn = QFrame()
            warn.setStyleSheet(
                "background:#e3b34120;border:1px solid #e3b34160;border-radius:8px;")
            wl = QHBoxLayout(warn)
            wl.setContentsMargins(16, 12, 16, 12)
            lbl = QLabel(
                "⚠  openrgb-python not installed.  "
                "Go to Settings → Dependencies → Install")
            lbl.setStyleSheet("color:#e3b341;font-size:13px;")
            wl.addWidget(lbl)
            layout.addWidget(warn)

        # Setup instructions card
        setup_card = _card()
        setup_l = QVBoxLayout(setup_card)
        setup_l.setContentsMargins(16, 14, 16, 16)
        setup_l.setSpacing(10)
        setup_l.addWidget(_section("SETUP REQUIRED"))

        steps = [
            ("1", "Download OpenRGB from openrgb.org and install it"),
            ("2", "Open OpenRGB → Settings → SDK Server → Enable Server"),
            ("3", "Leave OpenRGB running in the background"),
            ("4", "Click Connect below"),
        ]
        for num, text in steps:
            row = QHBoxLayout()
            num_lbl = QLabel(num)
            num_lbl.setFixedSize(20, 20)
            num_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            num_lbl.setStyleSheet(
                "background:#00d4aa;color:#0a0e14;border-radius:10px;"
                "font-size:11px;font-weight:bold;")
            row.addWidget(num_lbl)
            txt = QLabel(text)
            txt.setStyleSheet("color:#8b949e;font-size:13px;")
            row.addWidget(txt)
            row.addStretch()
            setup_l.addLayout(row)

        # Download button
        dl_btn = QPushButton("Download OpenRGB")
        dl_btn.setObjectName("secondary_btn")
        dl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dl_btn.clicked.connect(
            lambda: __import__("subprocess").Popen(
                ["explorer", "https://openrgb.org/releases.html"]))
        setup_l.addWidget(dl_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(setup_card)

        # Connection card
        conn_card = _card()
        conn_l = QVBoxLayout(conn_card)
        conn_l.setContentsMargins(16, 14, 16, 16)
        conn_l.setSpacing(12)
        conn_l.addWidget(_section("CONNECTION"))

        conn_row = QHBoxLayout()
        self.connect_btn = QPushButton("🔌  Connect to OpenRGB")
        self.connect_btn.setObjectName("primary_btn")
        self.connect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.connect_btn.clicked.connect(self._connect)
        conn_row.addWidget(self.connect_btn)

        self.conn_status = QLabel("Not connected — start OpenRGB first")
        self.conn_status.setStyleSheet("color:#484f58;font-size:12px;")
        conn_row.addWidget(self.conn_status)
        conn_row.addStretch()
        conn_l.addLayout(conn_row)
        layout.addWidget(conn_card)

        # Color controls (disabled until connected)
        color_card = _card()
        self.color_card = color_card
        cl = QVBoxLayout(color_card)
        cl.setContentsMargins(16, 14, 16, 16)
        cl.setSpacing(12)
        cl.addWidget(_section("GLOBAL COLOR"))

        color_row = QHBoxLayout()
        color_row.setSpacing(12)
        self.global_color_btn = ColorButton()
        color_row.addWidget(self.global_color_btn)
        color_row.addWidget(QLabel("Pick a color to apply to all RGB devices"))
        color_row.addStretch()

        apply_all_btn = QPushButton("Apply to All")
        apply_all_btn.setObjectName("primary_btn")
        apply_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_all_btn.clicked.connect(self._apply_global)
        color_row.addWidget(apply_all_btn)
        cl.addLayout(color_row)

        # Quick color swatches
        quick_row = QHBoxLayout()
        quick_row.setSpacing(8)
        for name, qcolor in [
            ("Teal",   QColor(0, 212, 170)),
            ("Red",    QColor(248, 81, 73)),
            ("Blue",   QColor(0, 180, 216)),
            ("Purple", QColor(168, 85, 247)),
            ("White",  QColor(255, 255, 255)),
            ("Off",    QColor(0, 0, 0)),
        ]:
            btn = ColorButton(qcolor)
            btn.setToolTip(name)
            r, g, b = qcolor.red(), qcolor.green(), qcolor.blue()
            btn.clicked.disconnect()
            btn.clicked.connect(lambda _, rv=r, gv=g, bv=b: self._apply_color(rv, gv, bv))
            quick_row.addWidget(btn)
        quick_row.addStretch()
        cl.addLayout(quick_row)

        # Effects
        cl.addWidget(_section("EFFECTS"))
        effects_row = QHBoxLayout()
        effects_row.setSpacing(10)
        for mode, label in [("static","Static"), ("breathing","Breathing"),
                             ("rainbow","Rainbow"), ("off","Turn Off")]:
            btn = QPushButton(label)
            btn.setObjectName("secondary_btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, m=mode: self._apply_mode(m))
            effects_row.addWidget(btn)
        effects_row.addStretch()
        cl.addLayout(effects_row)

        color_card.setEnabled(False)
        layout.addWidget(color_card)

        # Device list
        self.devices_card = _card()
        self.devices_layout = QVBoxLayout(self.devices_card)
        self.devices_layout.setContentsMargins(16, 12, 16, 12)
        placeholder = QLabel("Connect to OpenRGB to see your devices here")
        placeholder.setStyleSheet("color:#484f58;font-size:13px;padding:8px 0;")
        self.devices_layout.addWidget(placeholder)
        layout.addWidget(self.devices_card)
        layout.addStretch()

    def _connect(self):
        if not HAS_OPENRGB:
            self.conn_status.setText("Install openrgb-python first (Settings → Dependencies)")
            self.conn_status.setStyleSheet("color:#f85149;font-size:12px;")
            return

        self.connect_btn.setEnabled(False)
        self.connect_btn.setText("Connecting...")
        self.conn_status.setText("Trying localhost:6742...")

        def _do():
            try:
                client = OpenRGBClient()
                self._client = client
                self._devices = client.devices
                count = len(self._devices)
                self.connect_btn.setText("🔌  Connect to OpenRGB")
                self.connect_btn.setEnabled(True)
                self.conn_status.setText(f"✓ Connected — {count} device(s)")
                self.conn_status.setStyleSheet("color:#3fb950;font-size:12px;")
                self.color_card.setEnabled(True)
                self._populate_devices()
            except Exception as e:
                self.connect_btn.setText("🔌  Connect to OpenRGB")
                self.connect_btn.setEnabled(True)
                self.conn_status.setText(f"Failed: {e}")
                self.conn_status.setStyleSheet("color:#f85149;font-size:12px;")

        threading.Thread(target=_do, daemon=True).start()

    def _populate_devices(self):
        while self.devices_layout.count():
            item = self.devices_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._devices:
            lbl = QLabel("No RGB devices found")
            lbl.setStyleSheet("color:#484f58;")
            self.devices_layout.addWidget(lbl)
            return

        header = QLabel("PER-DEVICE CONTROL")
        header.setStyleSheet("color:#484f58;font-size:10px;font-weight:bold;letter-spacing:1.5px;")
        self.devices_layout.addWidget(header)

        for dev in self._devices:
            row = QHBoxLayout()
            name_lbl = QLabel(dev.name)
            name_lbl.setStyleSheet("color:#c9d1d9;font-size:13px;")
            name_lbl.setFixedWidth(220)
            row.addWidget(name_lbl)

            type_lbl = QLabel(str(dev.type).split(".")[-1])
            type_lbl.setStyleSheet("color:#484f58;font-size:11px;")
            row.addWidget(type_lbl)
            row.addStretch()

            col_btn = ColorButton()
            row.addWidget(col_btn)

            apply_btn = QPushButton("Apply")
            apply_btn.setObjectName("secondary_btn")
            apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            apply_btn.clicked.connect(
                lambda _, d=dev, b=col_btn: self._apply_to_device(d, b.get_rgb()))
            row.addWidget(apply_btn)

            wrapper = QWidget()
            wrapper.setLayout(row)
            self.devices_layout.addWidget(wrapper)

    def _apply_color(self, r, g, b):
        self.global_color_btn.set_color(QColor(r, g, b))
        if self._client:
            threading.Thread(
                target=lambda: self._client.set_color(RGBColor(r, g, b)),
                daemon=True).start()

    def _apply_global(self):
        r, g, b = self.global_color_btn.get_rgb()
        self._apply_color(r, g, b)

    def _apply_to_device(self, dev, rgb):
        if not self._client:
            return
        threading.Thread(
            target=lambda: dev.set_color(RGBColor(*rgb)),
            daemon=True).start()

    def _apply_mode(self, mode):
        if not self._client:
            return
        def _do():
            try:
                if mode == "off":
                    self._client.set_color(RGBColor(0, 0, 0))
                else:
                    for dev in self._devices:
                        try:
                            dev.set_mode(mode)
                        except Exception:
                            pass
            except Exception as e:
                print(f"RGB mode error: {e}")
        threading.Thread(target=_do, daemon=True).start()
