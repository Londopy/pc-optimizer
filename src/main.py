"""
PC Optimizer Pro - Main Entry Point
London's PC Optimizer | github.com/Londopy/pc-optimizer
"""
import sys
import os
import ctypes
import threading

# Must be first — request admin if not elevated
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def request_elevation():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable,
            " ".join([f'"{a}"' for a in sys.argv]), None, 1
        )
        sys.exit(0)

# Elevate before importing anything else
if sys.platform == "win32":
    request_elevation()

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from app_window import MainWindow
from tray import TrayManager


def main():
    # Enable High DPI
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("PC Optimizer Pro")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Londopy")
    app.setQuitOnLastWindowClosed(False)  # Keep alive in tray

    # Load icon
    icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Create main window
    window = MainWindow()

    # Create tray manager
    tray = TrayManager(window, app)

    # Show window on first launch
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
