"""
KOMALAM UI Styles
Modern dark and light QSS themes with rounded corners, gradients, and smooth animations.
"""

DARK_THEME = """
/* ========== Global ========== */
QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 14px;
}

/* ========== Main Window ========== */
QMainWindow {
    background-color: #1a1a2e;
}

QMainWindow::separator {
    width: 2px;
    background-color: #2a2a4a;
}

/* ========== Menu Bar ========== */
QMenuBar {
    background-color: #16213e;
    color: #e0e0e0;
    border-bottom: 1px solid #2a2a4a;
    padding: 4px;
}

QMenuBar::item:selected {
    background-color: #0f3460;
    border-radius: 4px;
}

QMenu {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    padding: 4px;
}

QMenu::item {
    padding: 8px 24px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #0f3460;
}

/* ========== Status Bar ========== */
QStatusBar {
    background-color: #16213e;
    color: #8888aa;
    border-top: 1px solid #2a2a4a;
    font-size: 12px;
    padding: 2px 8px;
}

/* ========== Scroll Areas ========== */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: #1a1a2e;
    width: 8px;
    border-radius: 4px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #3a3a5a;
    min-height: 30px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4a4a6a;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    height: 0px;
}

/* ========== Buttons ========== */
QPushButton {
    background-color: #0f3460;
    color: #e0e0e0;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #1a4a7a;
}

QPushButton:pressed {
    background-color: #0a2540;
}

QPushButton:disabled {
    background-color: #2a2a4a;
    color: #5a5a7a;
}

QPushButton#send_button {
    background-color: #e94560;
    color: white;
    border-radius: 20px;
    padding: 8px 16px;
    font-size: 16px;
    min-width: 40px;
    min-height: 40px;
}

QPushButton#send_button:hover {
    background-color: #ff5577;
}

QPushButton#send_button:pressed {
    background-color: #c93550;
}

QPushButton#new_chat_button {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #e94560, stop:1 #0f3460);
    color: white;
    border-radius: 10px;
    padding: 12px;
    font-size: 14px;
    font-weight: bold;
}

QPushButton#new_chat_button:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #ff5577, stop:1 #1a4a7a);
}

/* ========== Line Edit / Text Input ========== */
QLineEdit {
    background-color: #16213e;
    color: #e0e0e0;
    border: 2px solid #2a2a4a;
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 14px;
    selection-background-color: #0f3460;
}

QLineEdit:focus {
    border-color: #e94560;
}

QTextEdit {
    background-color: #16213e;
    color: #e0e0e0;
    border: 2px solid #2a2a4a;
    border-radius: 12px;
    padding: 12px;
    font-size: 14px;
    selection-background-color: #0f3460;
}

QTextEdit:focus {
    border-color: #e94560;
}

/* ========== Labels ========== */
QLabel {
    color: #e0e0e0;
    background-color: transparent;
}

QLabel#section_title {
    font-size: 12px;
    font-weight: bold;
    color: #8888aa;
    text-transform: uppercase;
    padding: 8px 4px 4px 4px;
}

QLabel#brand_title {
    font-size: 22px;
    font-weight: bold;
    color: #e94560;
    padding: 8px;
}

/* ========== Chat Bubbles ========== */
QFrame#user_bubble {
    background-color: #0f3460;
    border-radius: 16px;
    border-bottom-right-radius: 4px;
    padding: 12px 16px;
    margin: 4px 8px 4px 60px;
}

QFrame#assistant_bubble {
    background-color: #16213e;
    border: 1px solid #2a2a4a;
    border-radius: 16px;
    border-bottom-left-radius: 4px;
    padding: 12px 16px;
    margin: 4px 60px 4px 8px;
}

QLabel#bubble_text {
    color: #e0e0e0;
    font-size: 14px;
    line-height: 1.5;
    background-color: transparent;
}

QLabel#bubble_time {
    color: #5a5a7a;
    font-size: 11px;
    background-color: transparent;
}

/* ========== Sidebar ========== */
QFrame#sidebar {
    background-color: #16213e;
    border-right: 1px solid #2a2a4a;
}

/* ========== List Widget (Conversation History) ========== */
QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
}

QListWidget::item {
    background-color: transparent;
    color: #c0c0d0;
    padding: 12px 8px;
    border-radius: 8px;
    margin: 2px 4px;
}

QListWidget::item:hover {
    background-color: #1a2a4e;
}

QListWidget::item:selected {
    background-color: #0f3460;
    color: #ffffff;
}

/* ========== Combo Box ========== */
QComboBox {
    background-color: #16213e;
    color: #e0e0e0;
    border: 2px solid #2a2a4a;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
}

QComboBox:hover {
    border-color: #3a3a5a;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox QAbstractItemView {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #2a2a4a;
    selection-background-color: #0f3460;
    border-radius: 8px;
}

/* ========== Splitter ========== */
QSplitter::handle {
    background-color: #2a2a4a;
    width: 2px;
}

QSplitter::handle:hover {
    background-color: #e94560;
}

/* ========== Dialog ========== */
QDialog {
    background-color: #1a1a2e;
}

/* ========== Group Box ========== */
QGroupBox {
    font-weight: bold;
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    color: #8888aa;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}

/* ========== Check Box ========== */
QCheckBox {
    spacing: 8px;
    color: #e0e0e0;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 2px solid #3a3a5a;
    background-color: #16213e;
}

QCheckBox::indicator:checked {
    background-color: #e94560;
    border-color: #e94560;
}

/* ========== Slider ========== */
QSlider::groove:horizontal {
    height: 6px;
    background-color: #2a2a4a;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background-color: #e94560;
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}

QSlider::sub-page:horizontal {
    background-color: #e94560;
    border-radius: 3px;
}

/* ========== Spin Box ========== */
QSpinBox, QDoubleSpinBox {
    background-color: #16213e;
    color: #e0e0e0;
    border: 2px solid #2a2a4a;
    border-radius: 6px;
    padding: 6px;
}

/* ========== Progress Bar ========== */
QProgressBar {
    background-color: #2a2a4a;
    border-radius: 4px;
    text-align: center;
    color: #e0e0e0;
    font-size: 11px;
    height: 8px;
}

QProgressBar::chunk {
    background-color: #e94560;
    border-radius: 4px;
}

/* ========== Tab Widget ========== */
QTabWidget::pane {
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    background-color: #1a1a2e;
}

QTabBar::tab {
    background-color: #16213e;
    color: #8888aa;
    padding: 10px 20px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #1a1a2e;
    color: #e94560;
    border-bottom: 2px solid #e94560;
}

/* ========== Tooltip ========== */
QToolTip {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #2a2a4a;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

/* ========== Resource Monitor ========== */
QFrame#resource_frame {
    background-color: transparent;
    border: none;
}

QLabel#resource_label {
    font-size: 11px;
    color: #8888aa;
    background-color: transparent;
}

QProgressBar#resource_bar {
    max-height: 4px;
    min-height: 4px;
}
"""


LIGHT_THEME = """
/* ========== Global ========== */
QWidget {
    background-color: #f8f9fa;
    color: #2d3436;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 14px;
}

/* ========== Main Window ========== */
QMainWindow {
    background-color: #f8f9fa;
}

QMainWindow::separator {
    width: 2px;
    background-color: #dfe6e9;
}

/* ========== Menu Bar ========== */
QMenuBar {
    background-color: #ffffff;
    color: #2d3436;
    border-bottom: 1px solid #dfe6e9;
    padding: 4px;
}

QMenuBar::item:selected {
    background-color: #e8f0fe;
    border-radius: 4px;
}

QMenu {
    background-color: #ffffff;
    color: #2d3436;
    border: 1px solid #dfe6e9;
    border-radius: 8px;
    padding: 4px;
}

QMenu::item {
    padding: 8px 24px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #e8f0fe;
}

/* ========== Status Bar ========== */
QStatusBar {
    background-color: #ffffff;
    color: #636e72;
    border-top: 1px solid #dfe6e9;
    font-size: 12px;
    padding: 2px 8px;
}

/* ========== Scroll Areas ========== */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: #f8f9fa;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #b2bec3;
    min-height: 30px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background-color: #636e72;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    height: 0px;
}

/* ========== Buttons ========== */
QPushButton {
    background-color: #4361ee;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #3a56d4;
}

QPushButton:pressed {
    background-color: #2f47b8;
}

QPushButton:disabled {
    background-color: #dfe6e9;
    color: #b2bec3;
}

QPushButton#send_button {
    background-color: #e94560;
    color: white;
    border-radius: 20px;
    padding: 8px 16px;
    font-size: 16px;
    min-width: 40px;
    min-height: 40px;
}

QPushButton#send_button:hover {
    background-color: #ff5577;
}

QPushButton#new_chat_button {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #e94560, stop:1 #4361ee);
    color: white;
    border-radius: 10px;
    padding: 12px;
    font-size: 14px;
    font-weight: bold;
}

/* ========== Line Edit / Text Input ========== */
QLineEdit {
    background-color: #ffffff;
    color: #2d3436;
    border: 2px solid #dfe6e9;
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 14px;
    selection-background-color: #4361ee;
}

QLineEdit:focus {
    border-color: #4361ee;
}

QTextEdit {
    background-color: #ffffff;
    color: #2d3436;
    border: 2px solid #dfe6e9;
    border-radius: 12px;
    padding: 12px;
    font-size: 14px;
    selection-background-color: #4361ee;
}

QTextEdit:focus {
    border-color: #4361ee;
}

/* ========== Labels ========== */
QLabel {
    color: #2d3436;
    background-color: transparent;
}

QLabel#section_title {
    font-size: 12px;
    font-weight: bold;
    color: #636e72;
    padding: 8px 4px 4px 4px;
}

QLabel#brand_title {
    font-size: 22px;
    font-weight: bold;
    color: #e94560;
    padding: 8px;
}

/* ========== Chat Bubbles ========== */
QFrame#user_bubble {
    background-color: #4361ee;
    border-radius: 16px;
    border-bottom-right-radius: 4px;
    padding: 12px 16px;
    margin: 4px 8px 4px 60px;
}

QFrame#assistant_bubble {
    background-color: #ffffff;
    border: 1px solid #dfe6e9;
    border-radius: 16px;
    border-bottom-left-radius: 4px;
    padding: 12px 16px;
    margin: 4px 60px 4px 8px;
}

QLabel#bubble_text {
    font-size: 14px;
    line-height: 1.5;
    background-color: transparent;
}

QFrame#user_bubble QLabel#bubble_text {
    color: #ffffff;
}

QFrame#assistant_bubble QLabel#bubble_text {
    color: #2d3436;
}

QLabel#bubble_time {
    color: #b2bec3;
    font-size: 11px;
    background-color: transparent;
}

/* ========== Sidebar ========== */
QFrame#sidebar {
    background-color: #ffffff;
    border-right: 1px solid #dfe6e9;
}

/* ========== List Widget ========== */
QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
}

QListWidget::item {
    background-color: transparent;
    color: #2d3436;
    padding: 12px 8px;
    border-radius: 8px;
    margin: 2px 4px;
}

QListWidget::item:hover {
    background-color: #e8f0fe;
}

QListWidget::item:selected {
    background-color: #4361ee;
    color: #ffffff;
}

/* ========== Combo Box ========== */
QComboBox {
    background-color: #ffffff;
    color: #2d3436;
    border: 2px solid #dfe6e9;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #2d3436;
    border: 1px solid #dfe6e9;
    selection-background-color: #4361ee;
    selection-color: #ffffff;
    border-radius: 8px;
}

/* ========== Splitter ========== */
QSplitter::handle {
    background-color: #dfe6e9;
    width: 2px;
}

QSplitter::handle:hover {
    background-color: #4361ee;
}

/* ========== Dialog ========== */
QDialog {
    background-color: #f8f9fa;
}

/* ========== Group Box ========== */
QGroupBox {
    font-weight: bold;
    border: 1px solid #dfe6e9;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    color: #636e72;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}

/* ========== Check Box ========== */
QCheckBox {
    spacing: 8px;
    color: #2d3436;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 2px solid #b2bec3;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #4361ee;
    border-color: #4361ee;
}

/* ========== Slider ========== */
QSlider::groove:horizontal {
    height: 6px;
    background-color: #dfe6e9;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background-color: #4361ee;
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}

QSlider::sub-page:horizontal {
    background-color: #4361ee;
    border-radius: 3px;
}

/* ========== Spin Box ========== */
QSpinBox, QDoubleSpinBox {
    background-color: #ffffff;
    color: #2d3436;
    border: 2px solid #dfe6e9;
    border-radius: 6px;
    padding: 6px;
}

/* ========== Progress Bar ========== */
QProgressBar {
    background-color: #dfe6e9;
    border-radius: 4px;
    text-align: center;
    color: #2d3436;
    font-size: 11px;
    height: 8px;
}

QProgressBar::chunk {
    background-color: #4361ee;
    border-radius: 4px;
}

/* ========== Tab Widget ========== */
QTabWidget::pane {
    border: 1px solid #dfe6e9;
    border-radius: 8px;
    background-color: #f8f9fa;
}

QTabBar::tab {
    background-color: #ffffff;
    color: #636e72;
    padding: 10px 20px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #f8f9fa;
    color: #4361ee;
    border-bottom: 2px solid #4361ee;
}

/* ========== Tooltip ========== */
QToolTip {
    background-color: #ffffff;
    color: #2d3436;
    border: 1px solid #dfe6e9;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

/* ========== Resource Monitor ========== */
QFrame#resource_frame {
    background-color: transparent;
    border: none;
}

QLabel#resource_label {
    font-size: 11px;
    color: #636e72;
    background-color: transparent;
}

QProgressBar#resource_bar {
    max-height: 4px;
    min-height: 4px;
}
"""
