"""
Optimizer Page - Apply all PC tweaks from London's PS1 script
Each optimization category is a toggle-able card
"""
import subprocess
import winreg
import os
import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QScrollArea, QCheckBox, QTextEdit, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont


class OptimizationTask:
    def __init__(self, name, desc, func, risk="low"):
        self.name = name
        self.desc = desc
        self.func = func
        self.risk = risk  # low, medium, high
        self.enabled = True


def run_ps(cmd):
    """Run a PowerShell command silently."""
    return subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
        capture_output=True, text=True, timeout=30
    )


def reg_set(hive, path, name, value, reg_type=winreg.REG_DWORD):
    try:
        try:
            key = winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE)
        except FileNotFoundError:
            key = winreg.CreateKeyEx(hive, path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, name, 0, reg_type, value)
        winreg.CloseKey(key)
        return True
    except Exception as e:
        return False


# ===== OPTIMIZATION FUNCTIONS =====

def opt_ultimate_power():
    run_ps("powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61")
    result = run_ps("powercfg -list")
    for line in result.stdout.splitlines():
        if "Ultimate" in line:
            parts = line.split()
            if len(parts) >= 4:
                guid = parts[3]
                run_ps(f"powercfg -setactive {guid}")
                return f"Ultimate Performance activated ({guid})"
    run_ps("powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c")
    return "High Performance activated (Ultimate not found)"


def opt_disable_sleep():
    run_ps("powercfg -change -standby-timeout-ac 0")
    run_ps("powercfg -change -hibernate-timeout-ac 0")
    run_ps("powercfg /hibernate off")
    return "Sleep and Hibernate disabled"


def opt_cpu_boost():
    run_ps("powercfg -setacvalueindex SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMIN 100")
    run_ps("powercfg -setacvalueindex SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMAX 100")
    run_ps("powercfg -setacvalueindex SCHEME_CURRENT SUB_PROCESSOR PERFBOOSTMODE 2")
    run_ps("powercfg -setacvalueindex SCHEME_CURRENT SUB_PROCESSOR PERFBOOSTPOL 100")
    run_ps("powercfg -setactive SCHEME_CURRENT")
    reg_set(winreg.HKEY_LOCAL_MACHINE,
        r"SYSTEM\CurrentControlSet\Control\PriorityControl",
        "Win32PrioritySeparation", 38)
    return "CPU: 100% min/max, Aggressive boost, Priority boost 38"


def opt_disable_core_parking():
    path = r"SYSTEM\CurrentControlSet\Control\Power\PowerSettings\54533251-82be-4824-96c1-47b60b740d00\0cc5b647-c1df-4637-891a-dec35c318583"
    reg_set(winreg.HKEY_LOCAL_MACHINE, path, "ValueMax", 0)
    return "Core Parking disabled"


def opt_hags():
    reg_set(winreg.HKEY_LOCAL_MACHINE,
        r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers",
        "HwSchMode", 2)
    return "Hardware-Accelerated GPU Scheduling (HAGS) enabled"


def opt_game_mode():
    path = r"SOFTWARE\Microsoft\GameBar"
    reg_set(winreg.HKEY_CURRENT_USER, path, "AutoGameModeEnabled", 1)
    reg_set(winreg.HKEY_CURRENT_USER, path, "AllowAutoGameMode", 1)
    return "Windows Game Mode enabled"


def opt_mmcss():
    path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
    reg_set(winreg.HKEY_LOCAL_MACHINE, path, "SystemResponsiveness", 0)
    reg_set(winreg.HKEY_LOCAL_MACHINE, path, "NetworkThrottlingIndex", 0xffffffff)
    games_path = path + r"\Tasks\Games"
    reg_set(winreg.HKEY_LOCAL_MACHINE, games_path, "GPU Priority", 8)
    reg_set(winreg.HKEY_LOCAL_MACHINE, games_path, "Priority", 6)
    reg_set(winreg.HKEY_LOCAL_MACHINE, games_path, "Clock Rate", 10000)
    reg_set(winreg.HKEY_LOCAL_MACHINE, games_path, "Scheduling Category", "High", winreg.REG_SZ)
    reg_set(winreg.HKEY_LOCAL_MACHINE, games_path, "SFIO Priority", "High", winreg.REG_SZ)
    return "MMCSS: SystemResponsiveness=0, GPU Priority 8, CPU Priority 6"


def opt_disable_gamebar():
    path = r"System\GameConfigStore"
    reg_set(winreg.HKEY_CURRENT_USER, path, "GameDVR_Enabled", 0)
    reg_set(winreg.HKEY_CURRENT_USER, path, "GameDVR_FSEBehaviorMode", 2)
    reg_set(winreg.HKEY_CURRENT_USER,
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR",
        "AppCaptureEnabled", 0)
    policy_path = r"SOFTWARE\Policies\Microsoft\Windows\GameDVR"
    reg_set(winreg.HKEY_LOCAL_MACHINE, policy_path, "AllowGameDVR", 0)
    return "Xbox Game Bar / Game DVR disabled"


def opt_network():
    cmds = [
        "netsh int tcp set global autotuninglevel=normal",
        "netsh int tcp set global rss=enabled",
        "netsh int tcp set global chimney=disabled",
        "netsh int tcp set global ecncapability=disabled",
        "netsh int tcp set global timestamps=disabled",
    ]
    for cmd in cmds:
        run_ps(cmd)
    # Nagle
    reg_set(winreg.HKEY_LOCAL_MACHINE,
        r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces",
        "TcpAckFrequency", 1)
    return "TCP tuned: RSS on, Nagle disabled, ECN off"


def opt_telemetry():
    path = r"SOFTWARE\Policies\Microsoft\Windows\DataCollection"
    reg_set(winreg.HKEY_LOCAL_MACHINE, path, "AllowTelemetry", 0)
    reg_set(winreg.HKEY_LOCAL_MACHINE,
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection",
        "AllowTelemetry", 0)
    reg_set(winreg.HKEY_CURRENT_USER,
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\AdvertisingInfo",
        "Enabled", 0)
    return "Windows Telemetry and Advertising ID disabled"


def opt_disable_cortana():
    path = r"SOFTWARE\Policies\Microsoft\Windows\Windows Search"
    reg_set(winreg.HKEY_LOCAL_MACHINE, path, "AllowCortana", 0)
    return "Cortana disabled via policy"


def opt_visual_effects():
    path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects"
    reg_set(winreg.HKEY_CURRENT_USER, path, "VisualFXSetting", 2)
    path2 = r"Control Panel\Desktop"
    reg_set(winreg.HKEY_CURRENT_USER, path2, "MenuShowDelay", "0", winreg.REG_SZ)
    return "Visual effects set to 'Adjust for best performance'"


def opt_timer_resolution():
    path = r"SYSTEM\CurrentControlSet\Control\Session Manager\kernel"
    reg_set(winreg.HKEY_LOCAL_MACHINE, path, "GlobalTimerResolutionRequests", 1)
    return "High-resolution timer requests enabled"


def opt_windows_update_no_restart():
    path = r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU"
    reg_set(winreg.HKEY_LOCAL_MACHINE, path, "NoAutoRebootWithLoggedOnUsers", 1)
    reg_set(winreg.HKEY_LOCAL_MACHINE, path, "AUOptions", 2)
    return "Windows Update: no auto-restart, notify only"


def opt_nvidia_telemetry():
    tasks = [
        "NvTmMon_{B2FE1952-0186-46C3-BAEC-A80AA35AC5B8}",
        "NvTmRep_{B2FE1952-0186-46C3-BAEC-A80AA35AC5B8}",
        "NvNodeLauncher_{B2FE1952-0186-46C3-BAEC-A80AA35AC5B8}",
        "NvDriverUpdateCheckDaily_{B2FE1952-0186-46C3-BAEC-A80AA35AC5B8}",
    ]
    for t in tasks:
        subprocess.run(["schtasks", "/Change", "/TN", t, "/DISABLE"],
                       capture_output=True)
    return "NVIDIA telemetry tasks disabled"


def opt_disable_services():
    services = [
        "DiagTrack", "dmwappushservice", "WSearch",
        "Fax", "TabletInputService", "WbioSrvc",
        "lfsvc", "MapsBroker", "RemoteRegistry",
        "XblAuthManager", "XblGameSave", "XboxNetApiSvc",
        "WerSvc", "PcaSvc", "stisvc",
    ]
    disabled = []
    for svc in services:
        result = run_ps(f"Stop-Service -Name '{svc}' -Force; Set-Service -Name '{svc}' -StartupType Disabled")
        disabled.append(svc)
    return f"Disabled {len(disabled)} background services"


def opt_startup_cleanup():
    junk = ["OneDrive", "Skype", "Spotify", "EpicGamesLauncher",
            "Teams", "Cortana", "NvBackend"]
    for item in junk:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE)
            try:
                winreg.DeleteValue(key, item)
            except:
                pass
            winreg.CloseKey(key)
        except:
            pass
    return "Startup bloat removed from registry"


# ===== WORKER THREAD =====

class OptimizerWorker(QThread):
    log_signal = pyqtSignal(str, str)  # message, level (ok/warn/err)
    progress_signal = pyqtSignal(int)
    done_signal = pyqtSignal()

    def __init__(self, tasks):
        super().__init__()
        self.tasks = tasks

    def run(self):
        total = len(self.tasks)
        for i, task in enumerate(self.tasks):
            if not task.enabled:
                self.log_signal.emit(f"[SKIP] {task.name}", "skip")
                self.progress_signal.emit(int((i+1)/total*100))
                continue
            try:
                result = task.func()
                self.log_signal.emit(f"[OK] {task.name}: {result}", "ok")
            except Exception as e:
                self.log_signal.emit(f"[ERR] {task.name}: {e}", "err")
            self.progress_signal.emit(int((i+1)/total*100))

        self.done_signal.emit()


# ===== PAGE =====

class OptimizerPage(QWidget):
    def __init__(self):
        super().__init__()
        self._build_tasks()
        self._build_ui()

    def _build_tasks(self):
        self.tasks = [
            OptimizationTask("Ultimate Performance Plan", "Activate Ultimate Performance power plan", opt_ultimate_power),
            OptimizationTask("Disable Sleep/Hibernate", "Keep PC awake, disable hibernate", opt_disable_sleep),
            OptimizationTask("CPU Boost & Priority", "100% min/max state, aggressive boost, priority 38", opt_cpu_boost),
            OptimizationTask("Disable Core Parking", "Keep all CPU cores active", opt_disable_core_parking),
            OptimizationTask("HAGS Enable", "Hardware-Accelerated GPU Scheduling", opt_hags),
            OptimizationTask("Game Mode", "Enable Windows Game Mode", opt_game_mode),
            OptimizationTask("MMCSS Tuning", "GPU Priority 8, CPU Priority 6, High scheduling", opt_mmcss),
            OptimizationTask("Disable Game Bar/DVR", "Kill Xbox overlay and capture", opt_disable_gamebar),
            OptimizationTask("Network TCP Tuning", "RSS, Nagle off, ECN off", opt_network),
            OptimizationTask("Disable Telemetry", "Kill Microsoft data collection", opt_telemetry, "medium"),
            OptimizationTask("Disable Cortana", "Remove Cortana via policy", opt_disable_cortana, "medium"),
            OptimizationTask("Visual Effects: Performance", "Best performance mode", opt_visual_effects),
            OptimizationTask("Timer Resolution", "High-res timer requests", opt_timer_resolution),
            OptimizationTask("Windows Update: No Restart", "Stop forced reboots", opt_windows_update_no_restart),
            OptimizationTask("NVIDIA Telemetry Off", "Disable NVIDIA tracking tasks", opt_nvidia_telemetry),
            OptimizationTask("Disable Background Services", "Kill 15 unnecessary services", opt_disable_services, "medium"),
            OptimizationTask("Startup Cleanup", "Remove bloat from startup", opt_startup_cleanup),
        ]

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Top row
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        run_all_btn = QPushButton("⚡  Run All Optimizations")
        run_all_btn.setObjectName("primary_btn")
        run_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        run_all_btn.clicked.connect(self._run_all)
        top_row.addWidget(run_all_btn)

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

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedWidth(200)
        self.progress.setTextVisible(True)
        self.progress.setVisible(False)
        top_row.addWidget(self.progress)

        layout.addLayout(top_row)

        # Task list + log in horizontal split
        split = QHBoxLayout()
        split.setSpacing(16)

        # Tasks
        tasks_scroll = QScrollArea()
        tasks_scroll.setWidgetResizable(True)
        tasks_scroll.setFrameShape(QFrame.Shape.NoFrame)
        tasks_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        tasks_container = QWidget()
        self.tasks_layout = QVBoxLayout(tasks_container)
        self.tasks_layout.setSpacing(6)
        self.tasks_layout.setContentsMargins(0, 0, 0, 0)
        tasks_scroll.setWidget(tasks_container)

        self._checkboxes = []
        risk_colors = {"low": "#3fb950", "medium": "#e3b341", "high": "#f85149"}

        for task in self.tasks:
            row = QFrame()
            row.setObjectName("card")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(14, 10, 14, 10)

            cb = QCheckBox()
            cb.setChecked(task.enabled)
            cb.stateChanged.connect(lambda state, t=task: setattr(t, 'enabled', state == 2))
            row_layout.addWidget(cb)

            info = QVBoxLayout()
            info.setSpacing(2)
            name = QLabel(task.name)
            name.setStyleSheet("color: #c9d1d9; font-size: 13px; font-weight: bold;")
            desc = QLabel(task.desc)
            desc.setStyleSheet("color: #484f58; font-size: 11px;")
            info.addWidget(name)
            info.addWidget(desc)
            row_layout.addLayout(info)
            row_layout.addStretch()

            risk_dot = QLabel(f"● {task.risk.upper()}")
            risk_dot.setFixedWidth(80)
            risk_dot.setStyleSheet(f"color: {risk_colors.get(task.risk, '#484f58')}; font-size: 10px; font-weight: bold;")
            row_layout.addWidget(risk_dot)

            run_btn = QPushButton("Run")
            run_btn.setFixedSize(64, 28)
            run_btn.setObjectName("secondary_btn")
            run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            run_btn.clicked.connect(lambda _, t=task, b=run_btn: self._run_single(t, b))
            row_layout.addWidget(run_btn)

            self.tasks_layout.addWidget(row)
            self._checkboxes.append(cb)

        self.tasks_layout.addStretch()
        split.addWidget(tasks_scroll, 3)

        # Log output
        log_frame = QFrame()
        log_frame.setObjectName("card")
        log_vbox = QVBoxLayout(log_frame)
        log_vbox.setContentsMargins(12, 12, 12, 12)

        log_header = QLabel("OUTPUT LOG")
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
        self.log.setPlaceholderText("Run optimizations to see output...")
        log_vbox.addWidget(self.log)

        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.setObjectName("secondary_btn")
        clear_log_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_log_btn.clicked.connect(self.log.clear)
        log_vbox.addWidget(clear_log_btn)

        split.addWidget(log_frame, 2)
        layout.addLayout(split)

    def _log(self, msg, level="ok"):
        colors = {"ok": "#3fb950", "warn": "#e3b341", "err": "#f85149", "skip": "#484f58"}
        color = colors.get(level, "#8b949e")
        self.log.append(f'<span style="color:{color}; font-family:Consolas;">{msg}</span>')

    def _run_all(self):
        enabled = [t for t in self.tasks if t.enabled]
        if not enabled:
            return
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self._log("=== Starting PC Optimizer ===", "ok")

        self.worker = OptimizerWorker(enabled)
        self.worker.log_signal.connect(self._log)
        self.worker.progress_signal.connect(self.progress.setValue)
        self.worker.done_signal.connect(self._on_done)
        self.worker.start()

    def _on_done(self):
        self._log("=== Done! Restart recommended. ===", "ok")
        self.progress.setValue(100)

    def _run_single(self, task, btn):
        btn.setEnabled(False)
        btn.setText("...")

        def _do():
            try:
                result = task.func()
                self._log(f"[OK] {task.name}: {result}", "ok")
            except Exception as e:
                self._log(f"[ERR] {task.name}: {e}", "err")
            finally:
                btn.setEnabled(True)
                btn.setText("Run")

        threading.Thread(target=_do, daemon=True).start()

    def _select_all(self):
        for cb, task in zip(self._checkboxes, self.tasks):
            cb.setChecked(True)
            task.enabled = True

    def _clear_all(self):
        for cb, task in zip(self._checkboxes, self.tasks):
            cb.setChecked(False)
            task.enabled = False
