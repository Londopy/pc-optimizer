"""
Settings Page
"""
import subprocess
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QCheckBox, QComboBox, QScrollArea
)
from PyQt6.QtCore import Qt


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
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

        # About card
        about_card = QFrame()
        about_card.setObjectName("card_accent")
        about_card.setStyleSheet("QFrame#card_accent { background: #0d1117; border: 1px solid #00d4aa33; border-radius: 8px; }")
        about_l = QVBoxLayout(about_card)
        about_l.setContentsMargins(20, 18, 20, 18)
        about_l.setSpacing(8)

        title = QLabel("PC OPTIMIZER PRO")
        title.setStyleSheet("color: #00d4aa; font-size: 20px; font-weight: bold; font-family: Consolas; letter-spacing: 2px;")
        about_l.addWidget(title)

        ver = QLabel("Version 1.0.0  •  github.com/Londopy/pc-optimizer")
        ver.setStyleSheet("color: #484f58; font-size: 12px; font-family: Consolas;")
        about_l.addWidget(ver)

        desc = QLabel(
            "A professional PC optimization suite for Windows gaming rigs.\n"
            "Fan control via liquidctl • RGB via OpenRGB • Debloat • Registry tuning"
        )
        desc.setStyleSheet("color: #8b949e; font-size: 13px;")
        about_l.addWidget(desc)

        btn_row = QHBoxLayout()
        for label, url in [
            ("GitHub Repo", "https://github.com/Londopy/pc-optimizer"),
            ("Report Bug", "https://github.com/Londopy/pc-optimizer/issues"),
        ]:
            btn = QPushButton(label)
            btn.setObjectName("secondary_btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, u=url: subprocess.Popen(["start", u], shell=True))
            btn_row.addWidget(btn)
        btn_row.addStretch()
        about_l.addLayout(btn_row)
        layout.addWidget(about_card)

        # Startup settings
        section = QLabel("STARTUP & BEHAVIOR")
        section.setObjectName("section_header")
        layout.addWidget(section)

        startup_card = QFrame()
        startup_card.setObjectName("card")
        startup_l = QVBoxLayout(startup_card)
        startup_l.setContentsMargins(16, 14, 16, 14)
        startup_l.setSpacing(12)

        self.autostart_cb = QCheckBox("Start with Windows (launch minimized to tray)")
        self.autostart_cb.setChecked(self._get_autostart())
        self.autostart_cb.stateChanged.connect(self._toggle_autostart)
        startup_l.addWidget(self.autostart_cb)

        self.min_tray_cb = QCheckBox("Minimize to tray when closing window")
        self.min_tray_cb.setChecked(True)
        startup_l.addWidget(self.min_tray_cb)

        self.autorun_cb = QCheckBox("Apply optimizations automatically on startup")
        startup_l.addWidget(self.autorun_cb)

        layout.addWidget(startup_card)

        # Dependencies check
        section2 = QLabel("DEPENDENCIES")
        section2.setObjectName("section_header")
        layout.addWidget(section2)

        deps_card = QFrame()
        deps_card.setObjectName("card")
        deps_l = QVBoxLayout(deps_card)
        deps_l.setContentsMargins(16, 14, 16, 14)
        deps_l.setSpacing(8)

        deps = [
            ("psutil",          "CPU/RAM/process monitoring",   "pip install psutil"),
            ("pynvml",          "NVIDIA GPU stats",             "pip install pynvml"),
            ("liquidctl",       "Corsair AIO fan control",      "pip install liquidctl"),
            ("openrgb-python",  "RGB lighting control",         "pip install openrgb-python"),
            ("HardwareMonitor", "CPU/GPU temperatures",         "pip install HardwareMonitor"),
        ]

        for pkg, desc, install_cmd in deps:
            row = QHBoxLayout()
            row.setSpacing(12)

            # Check if installed
            try:
                __import__(pkg.replace("-", "_").replace(".", "_").split("-")[0])
                installed = True
            except ImportError:
                installed = False

            status = QLabel("✓" if installed else "✗")
            status.setFixedWidth(20)
            status.setStyleSheet(f"color: {'#3fb950' if installed else '#f85149'}; font-size: 14px; font-weight: bold;")
            row.addWidget(status)

            name_lbl = QLabel(pkg)
            name_lbl.setFixedWidth(160)
            name_lbl.setStyleSheet("color: #c9d1d9; font-size: 13px; font-weight: bold;")
            row.addWidget(name_lbl)

            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet("color: #484f58; font-size: 12px;")
            row.addWidget(desc_lbl)

            row.addStretch()

            if not installed:
                install_btn = QPushButton("Install")
                install_btn.setObjectName("primary_btn")
                install_btn.setFixedWidth(80)
                install_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                install_btn.clicked.connect(lambda _, cmd=install_cmd: self._install_package(cmd))
                row.addWidget(install_btn)

            deps_l.addLayout(row)

        layout.addWidget(deps_card)

        # NVRAM / reset section
        section3 = QLabel("DANGER ZONE")
        section3.setObjectName("section_header")
        layout.addWidget(section3)

        danger_card = QFrame()
        danger_card.setStyleSheet("QFrame { background: #0d1117; border: 1px solid #f8514944; border-radius: 8px; }")
        danger_l = QVBoxLayout(danger_card)
        danger_l.setContentsMargins(16, 14, 16, 14)
        danger_l.setSpacing(10)

        danger_lbl = QLabel("These actions modify system settings. Use with caution.")
        danger_lbl.setStyleSheet("color: #8b949e; font-size: 12px;")
        danger_l.addWidget(danger_lbl)

        danger_row = QHBoxLayout()
        export_btn = QPushButton("Export Registry Backup")
        export_btn.setObjectName("secondary_btn")
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.clicked.connect(self._export_backup)
        danger_row.addWidget(export_btn)

        restore_btn = QPushButton("Restore Power Defaults")
        restore_btn.setObjectName("danger_btn")
        restore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        restore_btn.clicked.connect(self._restore_defaults)
        danger_row.addWidget(restore_btn)

        danger_row.addStretch()
        danger_l.addLayout(danger_row)
        layout.addWidget(danger_card)
        layout.addStretch()

    def _get_autostart(self):
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_READ)
            winreg.QueryValueEx(key, "PCOptimizerPro")
            winreg.CloseKey(key)
            return True
        except:
            return False

    def _toggle_autostart(self, state):
        import winreg, sys
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE)
            if state == 2:  # checked
                exe = sys.executable
                winreg.SetValueEx(key, "PCOptimizerPro", 0, winreg.REG_SZ,
                                  f'"{exe}" --minimized')
            else:
                try:
                    winreg.DeleteValue(key, "PCOptimizerPro")
                except:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Autostart error: {e}")

    def _install_package(self, cmd):
        subprocess.Popen(f"start cmd /k {cmd}", shell=True)

    def _export_backup(self):
        result = subprocess.run(
            ["reg", "export", "HKLM\\SYSTEM\\CurrentControlSet\\Control",
             os.path.expanduser("~/Desktop/pc_optimizer_backup.reg"), "/y"],
            capture_output=True
        )

    def _restore_defaults(self):
        subprocess.run(["powercfg", "-restoredefaultschemes"], capture_output=True)
