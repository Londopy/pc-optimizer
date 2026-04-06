"""
Settings Page - fixed install buttons and dependency detection
"""
import subprocess
import sys
import os
import threading
import winreg
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QCheckBox, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal


class InstallWorker(QThread):
    done = pyqtSignal(str, bool)  # package name, success

    def __init__(self, pkg_spec, pkg_name):
        super().__init__()
        self.pkg_spec = pkg_spec
        self.pkg_name = pkg_name

    def run(self):
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", self.pkg_spec,
                 "--quiet", "--no-warn-script-location"],
                capture_output=True, text=True, timeout=120
            )
            self.done.emit(self.pkg_name, result.returncode == 0)
        except Exception as e:
            self.done.emit(self.pkg_name, False)


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self._install_workers = []
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

        # About card
        about_card = QFrame()
        about_card.setObjectName("card_accent")
        about_card.setStyleSheet(
            "QFrame#card_accent{background:#0d1117;border:1px solid #00d4aa33;border-radius:8px;}")
        about_l = QVBoxLayout(about_card)
        about_l.setContentsMargins(20, 18, 20, 18)
        about_l.setSpacing(8)

        title = QLabel("PC OPTIMIZER PRO")
        title.setStyleSheet(
            "color:#00d4aa;font-size:20px;font-weight:bold;font-family:Consolas;")
        about_l.addWidget(title)

        ver = QLabel("Version 1.0.0  •  github.com/Londopy/pc-optimizer")
        ver.setStyleSheet("color:#484f58;font-size:12px;font-family:Consolas;")
        about_l.addWidget(ver)

        desc = QLabel(
            "A professional PC optimization suite for Windows gaming rigs.\n"
            "Fan control via liquidctl  •  RGB via OpenRGB  •  Debloat  •  Registry tuning")
        desc.setStyleSheet("color:#8b949e;font-size:13px;")
        about_l.addWidget(desc)

        btn_row = QHBoxLayout()
        for label, url in [
            ("GitHub Repo",  "https://github.com/Londopy/pc-optimizer"),
            ("Report Bug",   "https://github.com/Londopy/pc-optimizer/issues"),
        ]:
            btn = QPushButton(label)
            btn.setObjectName("secondary_btn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, u=url: self._open_url(u))
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

        # Dependencies
        section2 = QLabel("DEPENDENCIES")
        section2.setObjectName("section_header")
        layout.addWidget(section2)

        deps_card = QFrame()
        deps_card.setObjectName("card")
        self.deps_layout = QVBoxLayout(deps_card)
        self.deps_layout.setContentsMargins(16, 14, 16, 14)
        self.deps_layout.setSpacing(8)
        layout.addWidget(deps_card)
        self._populate_deps()

        # Danger zone
        section3 = QLabel("DANGER ZONE")
        section3.setObjectName("section_header")
        layout.addWidget(section3)

        danger_card = QFrame()
        danger_card.setStyleSheet(
            "QFrame{background:#0d1117;border:1px solid #f8514944;border-radius:8px;}")
        danger_l = QVBoxLayout(danger_card)
        danger_l.setContentsMargins(16, 14, 16, 14)
        danger_l.setSpacing(10)

        danger_lbl = QLabel("These actions modify system settings. Use with caution.")
        danger_lbl.setStyleSheet("color:#8b949e;font-size:12px;")
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

    def _populate_deps(self):
        # Clear existing
        while self.deps_layout.count():
            item = self.deps_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        deps = [
            ("psutil",           "CPU/RAM/process monitoring",   "psutil>=5.9.0"),
            ("pynvml",           "NVIDIA GPU stats",             "pynvml>=11.5.0"),
            ("liquidctl",        "Fan control (Corsair/Lian Li)","liquidctl>=1.16.0"),
            ("openrgb",          "RGB lighting control",         "openrgb-python>=0.2.13"),
            ("HardwareMonitor",  "CPU/GPU temperatures",         "HardwareMonitor"),
        ]

        for pkg, desc, install_spec in deps:
            installed = self._check_installed(pkg)
            row = QHBoxLayout()
            row.setSpacing(12)

            status = QLabel("✓" if installed else "✗")
            status.setFixedWidth(20)
            status.setStyleSheet(
                f"color:{'#3fb950' if installed else '#f85149'};font-size:14px;font-weight:bold;")
            row.addWidget(status)

            name_lbl = QLabel(pkg)
            name_lbl.setFixedWidth(160)
            name_lbl.setStyleSheet("color:#c9d1d9;font-size:13px;font-weight:bold;")
            row.addWidget(name_lbl)

            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet("color:#484f58;font-size:12px;")
            row.addWidget(desc_lbl)
            row.addStretch()

            if not installed:
                install_btn = QPushButton("Install")
                install_btn.setObjectName("primary_btn")
                install_btn.setFixedWidth(80)
                install_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                install_btn.clicked.connect(
                    lambda _, s=install_spec, n=pkg, b=install_btn: self._install_pkg(s, n, b))
                row.addWidget(install_btn)

            wrapper = QWidget()
            wrapper.setLayout(row)
            self.deps_layout.addWidget(wrapper)

    def _check_installed(self, pkg):
        # Handle package name vs import name differences
        import_names = {
            "openrgb":          "openrgb",
            "HardwareMonitor":  "HardwareMonitor",
            "liquidctl":        "liquidctl",
            "psutil":           "psutil",
            "pynvml":           "pynvml",
        }
        try:
            __import__(import_names.get(pkg, pkg))
            return True
        except ImportError:
            return False

    def _install_pkg(self, spec, name, btn):
        btn.setText("...")
        btn.setEnabled(False)

        worker = InstallWorker(spec, name)
        worker.done.connect(lambda n, ok: self._on_install_done(n, ok))
        self._install_workers.append(worker)
        worker.start()

    def _on_install_done(self, name, success):
        if success:
            # Refresh the whole deps list to show updated status
            self._populate_deps()
        else:
            QMessageBox.warning(
                self, "Install Failed",
                f"Failed to install {name}.\n\n"
                f"Try manually in a terminal:\n"
                f"  pip install {name}\n\n"
                f"Make sure you're running as Administrator."
            )
            self._populate_deps()

    def _open_url(self, url):
        import subprocess
        subprocess.Popen(["explorer", url])

    def _get_autostart(self):
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
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE)
            if state == 2:
                winreg.SetValueEx(key, "PCOptimizerPro", 0, winreg.REG_SZ,
                    f'"{sys.executable}" "{os.path.abspath(__file__)}" --minimized')
            else:
                try:
                    winreg.DeleteValue(key, "PCOptimizerPro")
                except:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Autostart error: {e}")

    def _export_backup(self):
        try:
            dest = os.path.expanduser("~/Desktop/pc_optimizer_backup.reg")
            result = subprocess.run(
                ["reg", "export",
                 "HKLM\\SYSTEM\\CurrentControlSet\\Control", dest, "/y"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                QMessageBox.information(self, "Backup", f"Saved to:\n{dest}")
            else:
                QMessageBox.warning(self, "Backup Failed", result.stderr)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _restore_defaults(self):
        reply = QMessageBox.question(
            self, "Restore Defaults",
            "This will restore Windows default power plans.\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            subprocess.run(["powercfg", "-restoredefaultschemes"], capture_output=True)
            QMessageBox.information(self, "Done", "Power plans restored to defaults.")
