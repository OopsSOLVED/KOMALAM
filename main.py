"""
KOMALAM — Local AI Chatbot
Entry point for the desktop application.
"""

import sys
import os
import traceback

# Ensure the project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Pre-import torch BEFORE PyQt5 to avoid DLL load-order conflict on Windows.
# PyQt5 messes with the DLL search path which prevents torch's c10.dll from loading.
try:
    import torch  # noqa: F401
except ImportError:
    pass

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


def exception_hook(exc_type, exc_value, exc_tb):
    """Global fallback — log unhandled exceptions and show a crash dialog."""
    tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))

    # Write to stderr regardless
    sys.stderr.write(f"Unhandled exception:\n{tb_text}")

    try:
        app = QApplication.instance()
        if app:
            QMessageBox.critical(
                None,
                "KOMALAM Error",
                f"An unexpected error occurred:\n\n"
                f"{exc_type.__name__}: {exc_value}\n\n"
                f"Check data/komalam.log for details.",
            )
    except Exception:
        pass

    sys.__excepthook__(exc_type, exc_value, exc_tb)


def main():
    sys.excepthook = exception_hook

    # High-DPI scaling — must be set before QApplication is created
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("KOMALAM")
    app.setApplicationDisplayName("KOMALAM — Local AI Assistant")
    app.setFont(QFont("Segoe UI", 10))

    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
