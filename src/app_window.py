"""
Main Window - PC Optimizer Pro
Dark gaming aesthetic with sidebar navigation
Fixed: minimize crash on Windows with FramelessWindowHint
"""
import os
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon

from pages.dashboard import DashboardPage
from pages.optimizer import OptimizerPage
from pages.fan_control import FanControlPage
from pages.rgb_control import RGBPage
from pages.debloat import DebloatPage
from pages.settings import SettingsPage

STYLESHEET = """
* { box-sizing: border-box; }

QMainWindow, QWidget {
    background-color: #0a0e14;
    color: #c9d1d9;
    font-family: 'Segoe UI', 'Consolas';
    font-size: 13px;
}

#sidebar {
    background-color: #0d1117;
    border-right: 1px solid #161b22;
    min-width: 220px;
    max-width: 220px;
}

#logo_area {
    background-color: #0d1117;
    border-bottom: 1px solid #161b22;
    padding: 20px 16px;
}

#app_name {
    color: #ffffff;
    font-size: 15px;
    font-weight: bold;
    font-family: 'Consolas';
}

#app_sub {
    color: #484f58;
    font-size: 10px;
    font-family: 'Consolas';
}

QPushButton#nav_btn {
    background-color: transparent;
    border: none;
    border-left: 3px solid transparent;
    color: #8b949e;
    text-align: left;
    padding: 12px 16px 12px 20px;
    font-size: 13px;
    border-radius: 0px;
}

QPushButton#nav_btn:hover {
    background-color: #161b22;
    color: #c9d1d9;
    border-left: 3px solid #30363d;
}

QPushButton#nav_btn[active="true"] {
    background-color: #161b22;
    color: #00d4aa;
    border-left: 3px solid #00d4aa;
    font-weight: bold;
}

#content_area { background-color: #0a0e14; }

#top_bar {
    background-color: #0d1117;
    border-bottom: 1px solid #161b22;
    padding: 0px 24px;
    min-height: 56px;
    max-height: 56px;
}

#page_title {
    color: #ffffff;
    font-size: 18px;
    font-weight: bold;
}

#status_dot_green {
    background-color: #3fb950;
    border-radius: 4px;
    min-width: 8px; max-width: 8px;
    min-height: 8px; max-height: 8px;
}

#status_label { color: #8b949e; font-size: 12px; }

QPushButton#win_close {
    background-color: #ff5f57; border: none; border-radius: 6px;
    min-width: 12px; max-width: 12px; min-height: 12px; max-height: 12px;
}
QPushButton#win_close:hover { background-color: #ff3b30; }

QPushButton#win_min {
    background-color: #febc2e; border: none; border-radius: 6px;
    min-width: 12px; max-width: 12px; min-height: 12px; max-height: 12px;
}
QPushButton#win_min:hover { background-color: #e5a800; }

QPushButton#win_hide {
    background-color: #28c840; border: none; border-radius: 6px;
    min-width: 12px; max-width: 12px; min-height: 12px; max-height: 12px;
}
QPushButton#win_hide:hover { background-color: #1da032; }

QFrame#card {
    background-color: #0d1117;
    border: 1px solid #21262d;
    border-radius: 8px;
}

QFrame#card_accent {
    background-color: #0d1117;
    border: 1px solid #00d4aa44;
    border-radius: 8px;
}

QPushButton#primary_btn {
    background-color: #00d4aa; color: #0a0e14;
    border: none; border-radius: 6px;
    padding: 10px 24px; font-weight: bold; font-size: 13px;
}
QPushButton#primary_btn:hover { background-color: #00b894; }
QPushButton#primary_btn:pressed { background-color: #009d7f; }
QPushButton#primary_btn:disabled { background-color: #21262d; color: #484f58; }

QPushButton#danger_btn {
    background-color: #da3633; color: #ffffff;
    border: none; border-radius: 6px; padding: 10px 24px; font-weight: bold;
}
QPushButton#danger_btn:hover { background-color: #b91c1c; }

QPushButton#secondary_btn {
    background-color: transparent; color: #8b949e;
    border: 1px solid #30363d; border-radius: 6px; padding: 9px 20px;
}
QPushButton#secondary_btn:hover {
    background-color: #161b22; color: #c9d1d9; border-color: #484f58;
}

QProgressBar {
    border: 1px solid #21262d; border-radius: 4px;
    background-color: #161b22; text-align: center;
    color: #8b949e; font-size: 11px;
    min-height: 8px; max-height: 8px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00d4aa,stop:1 #00b4d8);
    border-radius: 3px;
}
QProgressBar#warn::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #e3b341,stop:1 #f0a500);
    border-radius: 3px;
}
QProgressBar#danger::chunk {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #f85149,stop:1 #da3633);
    border-radius: 3px;
}

QSlider::groove:horizontal { background:#21262d; height:6px; border-radius:3px; }
QSlider::handle:horizontal {
    background:#00d4aa; width:16px; height:16px;
    margin:-5px 0; border-radius:8px; border:2px solid #0a0e14;
}
QSlider::sub-page:horizontal {
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00d4aa,stop:1 #00b4d8);
    border-radius:3px;
}

QComboBox {
    background-color:#161b22; border:1px solid #30363d;
    border-radius:6px; color:#c9d1d9; padding:6px 12px;
    font-size:13px; min-width:140px;
}
QComboBox::drop-down { border:none; padding-right:10px; }
QComboBox QAbstractItemView {
    background-color:#161b22; border:1px solid #30363d;
    color:#c9d1d9; selection-background-color:#21262d;
}

QScrollBar:vertical { background:#0d1117; width:8px; border-radius:4px; }
QScrollBar::handle:vertical { background:#30363d; border-radius:4px; min-height:30px; }
QScrollBar::handle:vertical:hover { background:#484f58; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0px; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background:none; }

QLabel#section_header {
    color:#00d4aa; font-size:11px; font-weight:bold;
    letter-spacing:2px; font-family:'Consolas';
}
QLabel#metric_value {
    color:#ffffff; font-size:28px; font-weight:bold; font-family:'Consolas';
}

QCheckBox { color:#c9d1d9; spacing:8px; }
QCheckBox::indicator {
    width:16px; height:16px; border:1px solid #30363d;
    border-radius:3px; background-color:#161b22;
}
QCheckBox::indicator:checked { background-color:#00d4aa; border-color:#00d4aa; }
QCheckBox::indicator:hover { border-color:#00d4aa; }

QTextEdit {
    background-color:#010409; color:#3fb950;
    border:none; font-family:Consolas; font-size:12px;
}

QScrollArea { border:none; background:transparent; }

QLineEdit {
    background-color:#161b22; border:1px solid #30363d;
    border-radius:6px; color:#c9d1d9; padding:8px 12px;
}
QLineEdit:focus { border-color:#00d4aa; }

QSpinBox {
    background-color:#161b22; border:1px solid #30363d;
    border-radius:6px; color:#c9d1d9; padding:6px 8px;
}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PC Optimizer Pro")
        self.setMinimumSize(1100, 700)
        self.resize(1200, 760)

        # Use normal window flags — frameless causes minimize crash on Windows
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        self.setStyleSheet(STYLESHEET)
        self._drag_pos = None
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        right = QWidget()
        right.setObjectName("content_area")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.addWidget(self._build_topbar())

        self.pages = QStackedWidget()
        right_layout.addWidget(self.pages)
        root.addWidget(right)

        self._pages_map = {
            "Dashboard":    DashboardPage(),
            "Optimizer":    OptimizerPage(),
            "Fan Control":  FanControlPage(),
            "RGB / Lighting": RGBPage(),
            "Debloat":      DebloatPage(),
            "Settings":     SettingsPage(),
        }
        for page in self._pages_map.values():
            self.pages.addWidget(page)

        self._switch_page("Dashboard")

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        logo_area = QWidget()
        logo_area.setObjectName("logo_area")
        logo_area.setFixedHeight(72)
        logo_layout = QVBoxLayout(logo_area)
        logo_layout.setContentsMargins(20, 14, 20, 14)
        logo_layout.setSpacing(2)
        name_lbl = QLabel("PC OPTIMIZER")
        name_lbl.setObjectName("app_name")
        sub_lbl = QLabel("PRO v1.0")
        sub_lbl.setObjectName("app_sub")
        logo_layout.addWidget(name_lbl)
        logo_layout.addWidget(sub_lbl)
        layout.addWidget(logo_area)

        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background: #161b22;")
        layout.addWidget(line)

        nav_items = [
            ("Dashboard",     "⬡"),
            ("Optimizer",     "⚡"),
            ("Fan Control",   "❄"),
            ("RGB / Lighting","◈"),
            ("Debloat",       "◉"),
            ("Settings",      "⚙"),
        ]

        layout.addSpacing(8)
        self._nav_buttons = {}
        for label, icon in nav_items:
            btn = QPushButton(f"  {icon}   {label}")
            btn.setObjectName("nav_btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, l=label: self._switch_page(l))
            layout.addWidget(btn)
            self._nav_buttons[label] = btn

        layout.addStretch()

        ver_lbl = QLabel("Londopy/pc-optimizer")
        ver_lbl.setStyleSheet("color:#30363d;font-size:10px;padding:12px 20px;font-family:Consolas;")
        layout.addWidget(ver_lbl)
        return sidebar

    def _build_topbar(self):
        bar = QWidget()
        bar.setObjectName("top_bar")
        bar.setFixedHeight(56)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 0, 16, 0)

        self.page_title_lbl = QLabel("Dashboard")
        self.page_title_lbl.setObjectName("page_title")
        layout.addWidget(self.page_title_lbl)
        layout.addStretch()

        dot = QWidget()
        dot.setObjectName("status_dot_green")
        dot.setFixedSize(8, 8)
        layout.addWidget(dot)
        status = QLabel("Optimized")
        status.setObjectName("status_label")
        layout.addWidget(status)
        layout.addSpacing(24)

        # Window controls — use native actions, no frameless tricks
        hide_btn = QPushButton()
        hide_btn.setObjectName("win_hide")
        hide_btn.setFixedSize(12, 12)
        hide_btn.setToolTip("Hide to tray")
        hide_btn.clicked.connect(self._hide_to_tray)
        hide_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        min_btn = QPushButton()
        min_btn.setObjectName("win_min")
        min_btn.setFixedSize(12, 12)
        min_btn.setToolTip("Minimize")
        min_btn.clicked.connect(self._safe_minimize)
        min_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        close_btn = QPushButton()
        close_btn.setObjectName("win_close")
        close_btn.setFixedSize(12, 12)
        close_btn.setToolTip("Close")
        close_btn.clicked.connect(self._hide_to_tray)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        layout.addWidget(hide_btn)
        layout.addSpacing(6)
        layout.addWidget(min_btn)
        layout.addSpacing(6)
        layout.addWidget(close_btn)
        return bar

    def _switch_page(self, name):
        if name not in self._pages_map:
            return
        for label, btn in self._nav_buttons.items():
            btn.setProperty("active", label == name)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.pages.setCurrentWidget(self._pages_map[name])
        self.page_title_lbl.setText(name)

    def _hide_to_tray(self):
        self.hide()

    def _safe_minimize(self):
        # Restore normal window flags temporarily so minimize works
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        self.show()
        self.showMinimized()

    def changeEvent(self, event):
        # Restore from taskbar click
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.WindowStateChange:
            if self.windowState() == Qt.WindowState.WindowNoState:
                self.show()
        super().changeEvent(event)
