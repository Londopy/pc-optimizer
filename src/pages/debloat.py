"""
Debloat Page - Remove Windows bloatware and telemetry
"""
import subprocess
import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QCheckBox, QTextEdit, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# Packages: (display_name, package_name, safe_to_remove)
BLOATWARE = [
    # Microsoft Apps
    ("Xbox App",                "Microsoft.XboxApp",                 True),
    ("Xbox Game Bar",           "Microsoft.XboxGamingOverlay",       True),
    ("Xbox Game Overlay",       "Microsoft.XboxGameOverlay",         True),
    ("Xbox Identity Provider",  "Microsoft.XboxIdentityProvider",    True),
    ("Xbox Speech To Text",     "Microsoft.XboxSpeechToTextOverlay", True),
    ("Cortana",                 "Microsoft.549981C3F5F10",           True),
    ("3D Viewer",               "Microsoft.Microsoft3DViewer",       True),
    ("3D Builder",              "Microsoft.3DBuilder",               True),
    ("Mixed Reality Portal",    "Microsoft.MixedReality.Portal",     True),
    ("OneNote (Store)",         "Microsoft.Office.OneNote",          False),
    ("OneDrive",                "Microsoft.OneDriveSync",            False),
    ("Teams (Personal)",        "MicrosoftTeams",                    True),
    ("Your Phone",              "Microsoft.YourPhone",               True),
    ("People",                  "Microsoft.People",                  True),
    ("Mail & Calendar",         "microsoft.windowscommunicationsapps", False),
    ("Maps",                    "Microsoft.WindowsMaps",             True),
    ("Alarms & Clock",          "Microsoft.WindowsAlarms",           True),
    ("Feedback Hub",            "Microsoft.WindowsFeedbackHub",      True),
    ("Get Help",                "Microsoft.GetHelp",                 True),
    ("Tips",                    "Microsoft.Getstarted",              True),
    ("Movies & TV",             "Microsoft.ZuneVideo",               True),
    ("Groove Music",            "Microsoft.ZuneMusic",               True),
    ("MSN Weather",             "Microsoft.BingWeather",             True),
    ("MSN News",                "Microsoft.BingNews",                True),
    ("Power Automate",          "Microsoft.PowerAutomateDesktop",    True),
    ("Quick Assist",            "MicrosoftCorporationII.QuickAssist", True),
    ("To Do",                   "Microsoft.Todos",                   False),
    ("Solitaire Collection",    "Microsoft.MicrosoftSolitaireCollection", True),
    # OEM/third-party
    ("Candy Crush",             "king.com.CandyCrushSaga",           True),
    ("Candy Crush Friends",     "king.com.CandyCrushFriendsSaga",    True),
    ("Bubble Witch",            "king.com.BubbleWitch3Saga",         True),
    ("Spotify (Store)",         "SpotifyAB.SpotifyMusic",            False),
    ("Disney+",                 "Disney.37853D22215B2",              True),
    ("Netflix",                 "4DF9E0F8.Netflix",                  False),
    ("TikTok",                  "BytedancePte.Ltd.TikTok",           True),
    ("Clipchamp",               "Clipchamp.Clipchamp",               True),
    ("Family Safety",           "MicrosoftCorporationII.MicrosoftFamily", True),
]


class DebloatWorker(QThread):
    log_signal = pyqtSignal(str, str)
    progress_signal = pyqtSignal(int, int)
    done_signal = pyqtSignal()

    def __init__(self, packages):
        super().__init__()
        self.packages = packages

    def run(self):
        total = len(self.packages)
        for i, (name, pkg) in enumerate(self.packages):
            self.log_signal.emit(f"Removing {name}...", "info")
            try:
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command",
                     f"Get-AppxPackage -AllUsers *{pkg}* | Remove-AppxPackage -ErrorAction SilentlyContinue; "
                     f"Get-AppxProvisionedPackage -Online | Where-Object {{$_.PackageName -like '*{pkg}*'}} | "
                     f"Remove-AppxProvisionedPackage -Online -ErrorAction SilentlyContinue"],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    self.log_signal.emit(f"  ✓ Removed: {name}", "ok")
                else:
                    self.log_signal.emit(f"  ? Not found or already removed: {name}", "skip")
            except subprocess.TimeoutExpired:
                self.log_signal.emit(f"  ✗ Timeout: {name}", "err")
            except Exception as e:
                self.log_signal.emit(f"  ✗ Error {name}: {e}", "err")
            self.progress_signal.emit(i + 1, total)

        self.done_signal.emit()


class DebloatPage(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header + controls
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        remove_btn = QPushButton("🗑  Remove Selected")
        remove_btn.setObjectName("danger_btn")
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_btn.clicked.connect(self._run_debloat)
        top_row.addWidget(remove_btn)

        safe_only_btn = QPushButton("✓ Select Safe Only")
        safe_only_btn.setObjectName("secondary_btn")
        safe_only_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        safe_only_btn.clicked.connect(self._select_safe)
        top_row.addWidget(safe_only_btn)

        select_all_btn = QPushButton("Select All")
        select_all_btn.setObjectName("secondary_btn")
        select_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        select_all_btn.clicked.connect(self._select_all)
        top_row.addWidget(select_all_btn)

        clear_btn = QPushButton("Clear All")
        clear_btn.setObjectName("secondary_btn")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_all)
        top_row.addWidget(clear_btn)

        top_row.addStretch()

        warning = QLabel("⚠  Some apps may not reinstall without a Windows reset")
        warning.setStyleSheet("color: #e3b341; font-size: 12px;")
        top_row.addWidget(warning)

        layout.addLayout(top_row)

        # Split: package list + log
        split = QHBoxLayout()
        split.setSpacing(16)

        # Package list
        pkg_scroll = QScrollArea()
        pkg_scroll.setWidgetResizable(True)
        pkg_scroll.setFrameShape(QFrame.Shape.NoFrame)
        pkg_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        pkg_container = QWidget()
        self.pkg_layout = QVBoxLayout(pkg_container)
        self.pkg_layout.setSpacing(4)
        self.pkg_layout.setContentsMargins(0, 0, 0, 0)
        pkg_scroll.setWidget(pkg_container)

        self._checkboxes = []
        self._package_data = []

        # Group by category
        categories = {
            "Microsoft": [b for b in BLOATWARE if b[1].startswith("Microsoft") or b[1].startswith("microsoft")],
            "Xbox": [b for b in BLOATWARE if "Xbox" in b[0] or "xbox" in b[1].lower()],
            "Games & Entertainment": [b for b in BLOATWARE if b[1].startswith("king.") or b[1] in
                                       ["4DF9E0F8.Netflix", "Disney.37853D22215B2", "BytedancePce.Ltd.TikTok",
                                        "Microsoft.MicrosoftSolitaireCollection"]],
            "Other": [],
        }
        # Simple flat approach
        for name, pkg, safe in BLOATWARE:
            row = QFrame()
            row.setObjectName("card")
            row.setFixedHeight(44)
            row_l = QHBoxLayout(row)
            row_l.setContentsMargins(12, 8, 12, 8)

            cb = QCheckBox()
            cb.setChecked(False)
            row_l.addWidget(cb)

            name_lbl = QLabel(name)
            name_lbl.setStyleSheet("color: #c9d1d9; font-size: 13px;")
            name_lbl.setFixedWidth(200)
            row_l.addWidget(name_lbl)

            pkg_lbl = QLabel(pkg)
            pkg_lbl.setStyleSheet("color: #484f58; font-size: 11px; font-family: Consolas;")
            row_l.addWidget(pkg_lbl)

            row_l.addStretch()

            safe_lbl = QLabel("SAFE" if safe else "CAUTION")
            safe_lbl.setStyleSheet(
                "color: #3fb950; font-size: 10px; font-weight: bold; letter-spacing: 1px;"
                if safe else
                "color: #e3b341; font-size: 10px; font-weight: bold; letter-spacing: 1px;"
            )
            row_l.addWidget(safe_lbl)

            self.pkg_layout.addWidget(row)
            self._checkboxes.append(cb)
            self._package_data.append((name, pkg, safe))

        self.pkg_layout.addStretch()
        split.addWidget(pkg_scroll, 3)

        # Log
        log_frame = QFrame()
        log_frame.setObjectName("card")
        log_vbox = QVBoxLayout(log_frame)
        log_vbox.setContentsMargins(12, 12, 12, 12)

        log_header = QLabel("REMOVAL LOG")
        log_header.setObjectName("section_header")
        log_vbox.addWidget(log_header)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("""
            QTextEdit {
                background-color: #010409;
                color: #3fb950;
                border: none;
                font-family: Consolas;
                font-size: 12px;
            }
        """)
        log_vbox.addWidget(self.log)

        split.addWidget(log_frame, 2)
        layout.addLayout(split)

    def _log(self, msg, level="info"):
        colors = {"ok": "#3fb950", "err": "#f85149", "skip": "#484f58", "info": "#8b949e"}
        c = colors.get(level, "#8b949e")
        self.log.append(f'<span style="color:{c}; font-family:Consolas;">{msg}</span>')

    def _run_debloat(self):
        selected = [(name, pkg) for cb, (name, pkg, safe) in zip(self._checkboxes, self._package_data) if cb.isChecked()]
        if not selected:
            self._log("No packages selected.", "skip")
            return
        self._log(f"=== Removing {len(selected)} packages ===", "info")
        self.worker = DebloatWorker(selected)
        self.worker.log_signal.connect(self._log)
        self.worker.done_signal.connect(lambda: self._log("=== Done ===", "ok"))
        self.worker.start()

    def _select_safe(self):
        for cb, (_, _, safe) in zip(self._checkboxes, self._package_data):
            cb.setChecked(safe)

    def _select_all(self):
        for cb in self._checkboxes:
            cb.setChecked(True)

    def _clear_all(self):
        for cb in self._checkboxes:
            cb.setChecked(False)
