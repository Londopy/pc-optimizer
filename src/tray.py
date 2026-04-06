"""
System Tray Manager
Handles minimize-to-tray, context menu, and notifications
"""
import os
import threading
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QObject, pyqtSignal


class TrayManager(QObject):
    show_window_signal = pyqtSignal()

    def __init__(self, window, app):
        super().__init__()
        self.window = window
        self.app = app

        # Load icon
        icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icon.ico")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
        else:
            icon = app.style().standardIcon(app.style().StandardPixmap.SP_ComputerIcon)

        self.tray = QSystemTrayIcon(icon, app)
        self.tray.setToolTip("PC Optimizer Pro — Running")

        # Build context menu
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #0d1117;
                border: 1px solid #30363d;
                color: #c9d1d9;
                padding: 4px 0px;
                font-family: 'Segoe UI';
                font-size: 13px;
            }
            QMenu::item {
                padding: 8px 20px;
            }
            QMenu::item:selected {
                background-color: #161b22;
                color: #00d4aa;
            }
            QMenu::separator {
                height: 1px;
                background: #21262d;
                margin: 4px 0px;
            }
        """)

        self.action_show = QAction("⬡  Show PC Optimizer")
        self.action_show.triggered.connect(self.show_window)
        menu.addAction(self.action_show)

        menu.addSeparator()

        action_optimizer = QAction("⚡  Run Optimizer")
        action_optimizer.triggered.connect(self.run_optimizer)
        menu.addAction(action_optimizer)

        action_fan = QAction("❄  Fan Control")
        action_fan.triggered.connect(lambda: self._show_page("Fan Control"))
        menu.addAction(action_fan)

        menu.addSeparator()

        action_quit = QAction("✕  Quit")
        action_quit.triggered.connect(self.quit_app)
        menu.addAction(action_quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def show_window(self):
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.window.isVisible():
                self.window.hide()
            else:
                self.show_window()

    def _show_page(self, page_name):
        self.show_window()
        if hasattr(self.window, '_switch_page'):
            self.window._switch_page(page_name)

    def run_optimizer(self):
        self._show_page("Optimizer")

    def notify(self, title, message):
        self.tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3000)

    def quit_app(self):
        self.tray.hide()
        self.app.quit()
