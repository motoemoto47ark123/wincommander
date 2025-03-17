import sys
import subprocess
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QListWidget, QLabel, QLineEdit, QPushButton, QDesktopWidget, 
                            QTextEdit, QAbstractItemView, QFrame, QGraphicsDropShadowEffect)
from PyQt5.QtGui import QFont, QColor, QIcon, QPainter, QPen, QPixmap
from ctypes import windll
from PyQt5.QtCore import QTimer, QThreadPool, QRunnable, pyqtSignal, QObject, Qt, QSize, QPropertyAnimation, QEasingCurve, QPointF
import os
import json
import math
import urllib.request

# Setup logging
log_directory = os.path.join("C:", os.sep, "Users", "Public", "Documents", "wincommander")
if not os.path.exists(log_directory):
    os.makedirs(log_directory)
log_filename = os.path.join(log_directory, 'wincommander.log')
logging.basicConfig(filename=log_filename, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def is_admin():
    try:
        return windll.shell32.IsUserAnAdmin()
    except Exception as e:
        logging.error("Error checking administrator privileges: {}".format(e))
        return False

def run_as_admin(command):
    """Run a command with administrative privileges"""
    try:
        if sys.platform == 'win32':
            # Create a VBS script that will run the command with elevated privileges
            vbs_content = f'''
Set UAC = CreateObject("Shell.Application")
UAC.ShellExecute "cmd.exe", "/c {command}", "", "runas", 1
'''
            # Write the VBS script to a temporary file
            vbs_path = os.path.join(os.environ.get('TEMP', ''), 'run_elevated.vbs')
            with open(vbs_path, 'w') as f:
                f.write(vbs_content)
            
            # Execute the VBS script
            subprocess.Popen(['cscript.exe', '//Nologo', vbs_path], shell=True)
            
            # Schedule deletion of the temporary file
            QTimer.singleShot(5000, lambda: os.remove(vbs_path) if os.path.exists(vbs_path) else None)
            
            logging.info(f"Executed command with elevation: {command}")
            return True
    except Exception as e:
        logging.error(f"Error running command as admin: {e}")
        return False

def load_commands_from_json():
    """Load commands from the JSON file on the web server."""
    try:
        # URL for the commands JSON data
        url = "http://db227.motoemotovps.xyz/windows_commands.json"
        
        # Set up a request with a timeout
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'WinCommander/1.0'}
        )
        
        # Fetch data from the URL with a 10 second timeout
        with urllib.request.urlopen(req, timeout=10) as response:
            # Read and decode the JSON data
            json_data = response.read().decode('utf-8')
            data = json.loads(json_data)
            commands = data.get('commands', [])
            
            logging.info(f"Successfully loaded {len(commands)} commands from online source")
            
            # Process the commands as before
            return {cmd['name']: {
                'title': cmd['name'],
                'info': cmd['description'] + "\n\n" + cmd['notes'],
                'command': cmd['command'],
                'admin_required': cmd['admin_required'],
                'category': cmd.get('category', 'system').lower()
            } for cmd in commands}
    
    except Exception as e:
        logging.error(f"Error loading commands from web: {e}")
        return {}

class CommandSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)

class CommandRunner(QRunnable):
    def __init__(self, command, admin_required):
        super().__init__()
        self.command = command
        self.admin_required = admin_required
        self.signals = CommandSignals()

    def run(self):
        try:
            if self.admin_required and not is_admin():
                # Run with admin privileges
                success = run_as_admin(self.command)
                if not success:
                    raise Exception("Failed to run command with admin privileges")
            else:
                # Run without admin privileges
                subprocess.Popen(self.command, shell=True)

            self.signals.finished.emit()
        except Exception as e:
            self.signals.error.emit(str(e))

# Custom Title Bar for Windows Dark Mode
class TitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(34)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Title icon and text
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)
        
        # Create app icon using the actual .ico file
        app_icon = QLabel()
        icon = QIcon("wincommander.ico")
        pixmap = icon.pixmap(16, 16)
        app_icon.setPixmap(pixmap)
        title_layout.addWidget(app_icon)
        
        app_title = QLabel("WinCommander")
        app_title.setStyleSheet("color: #cdd6f4; font-size: 12px; font-weight: bold;")
        title_layout.addWidget(app_title)
        
        # Add title container to main layout with stretch to push buttons to right
        self.layout.addWidget(title_container)
        self.layout.addStretch(1)  # This pushes everything after it to the right
        
        # Create window control buttons
        self.minimize_button = QPushButton(self)
        self.minimize_button.setFixedSize(46, 34)
        self.minimize_button.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 0px;
                background-color: transparent;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #3c3e4f;
            }
            QPushButton:pressed {
                background-color: #313244;
            }
        """)
        self.minimize_button.clicked.connect(self.parent.showMinimized)
        self.minimize_button.setToolTip("Minimize")
        
        # Maximize button
        self.maximize_button = QPushButton(self)
        self.maximize_button.setFixedSize(46, 34)
        self.maximize_button.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 0px;
                background-color: transparent;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #3c3e4f;
            }
            QPushButton:pressed {
                background-color: #313244;
            }
        """)
        self.maximize_button.clicked.connect(self.toggle_maximize)
        self.maximize_button.setToolTip("Maximize")
        
        # Close button
        self.close_button = QPushButton(self)
        self.close_button.setFixedSize(46, 34)
        self.close_button.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 0px;
                background-color: transparent;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #e64553;
            }
            QPushButton:pressed {
                background-color: #d20f2c;
            }
        """)
        self.close_button.clicked.connect(self.parent.close)
        self.close_button.setToolTip("Close")
        
        # Add buttons directly to the main layout in the correct order
        self.layout.addWidget(self.minimize_button)
        self.layout.addWidget(self.maximize_button)
        self.layout.addWidget(self.close_button)
        
    def toggle_maximize(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
            self.maximize_button.setToolTip("Maximize")
        else:
            self.parent.showMaximized()
            self.maximize_button.setToolTip("Restore")
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.parent.windowHandle().startSystemMove()
    
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle_maximize()
    
    def resizeEvent(self, event):
        # Update the icons on resize
        self.update()
        super().resizeEvent(event)
    
    def paintEvent(self, event):
        # Draw the title bar background
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw bottom border
        painter.setPen(QPen(QColor("#313244"), 1))
        painter.drawLine(0, self.height()-1, self.width(), self.height()-1)
        
        # Draw the window controls
        # Minimize button
        min_x = self.minimize_button.x() + self.minimize_button.width() // 2
        min_y = self.minimize_button.y() + self.minimize_button.height() // 2
        painter.setPen(QPen(QColor("#cdd6f4"), 1))
        painter.drawLine(min_x - 9, min_y, min_x + 9, min_y)
        
        # Maximize/Restore button
        max_x = self.maximize_button.x() + self.maximize_button.width() // 2
        max_y = self.maximize_button.y() + self.maximize_button.height() // 2
        
        if self.parent.isMaximized():
            # Draw restore icon (nested rectangles)
            painter.drawRect(max_x - 5, max_y - 7, 10, 10)
            painter.drawRect(max_x - 8, max_y - 4, 10, 10)
            painter.drawLine(max_x - 5, max_y - 7, max_x - 5, max_y - 4)
            painter.drawLine(max_x + 5, max_y - 7, max_x + 5, max_y - 4)
            painter.drawLine(max_x - 8, max_y + 6, max_x - 5, max_y + 6)
            painter.drawLine(max_x - 8, max_y - 4, max_x - 8, max_y + 6)
        else:
            # Draw maximize icon (simple rectangle)
            painter.drawRect(max_x - 9, max_y - 9, 18, 18)
        
        # Close button
        close_x = self.close_button.x() + self.close_button.width() // 2
        close_y = self.close_button.y() + self.close_button.height() // 2
        
        # Change color for close button
        if self.close_button.underMouse():
            painter.setPen(QPen(QColor("white"), 1))
        else:
            painter.setPen(QPen(QColor("#cdd6f4"), 1))
            
        # Draw X
        painter.drawLine(close_x - 9, close_y - 9, close_x + 9, close_y + 9)
        painter.drawLine(close_x + 9, close_y - 9, close_x - 9, close_y + 9)

# Loading Animation
class LoadingAnimation(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_angle)
        self.active = False
        self.dots = 3
        self.dot_radius = 3
        self.color = QColor("#89b4fa")
        
    def start_animation(self):
        self.active = True
        self.timer.start(50)
        self.show()
        
    def stop_animation(self):
        self.active = False
        self.timer.stop()
        self.hide()
        
    def update_angle(self):
        self.angle = (self.angle + 10) % 360
        self.update()
        
    def paintEvent(self, event):
        if not self.active:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = min(center_x, center_y) - self.dot_radius
        
        for i in range(self.dots):
            angle = self.angle + (i * (360 / self.dots))
            x = center_x + radius * 0.7 * math.cos(math.radians(angle))
            y = center_y + radius * 0.7 * math.sin(math.radians(angle))
            
            alpha = 255 - (i * (200 // self.dots))
            color = QColor(self.color)
            color.setAlpha(alpha)
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            
            painter.drawEllipse(QPointF(x, y), self.dot_radius, self.dot_radius)

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_command_running = False
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.init_ui()

    def init_ui(self):
        # Set application style and theme
        self.setWindowTitle("WinCommander")
        self.setGeometry(0, 0, 1000, 700)
        self.center_on_screen()
        
        # Main container with shadow effect
        main_container = QWidget()
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 0)
        main_container.setGraphicsEffect(shadow)
        
        # Main container layout
        main_container_layout = QVBoxLayout(main_container)
        main_container_layout.setContentsMargins(0, 0, 0, 0)
        main_container_layout.setSpacing(0)
        
        # App container (white background with rounded corners)
        app_container = QWidget()
        app_container.setObjectName("appContainer")
        app_container.setStyleSheet("""
            #appContainer {
                background-color: #1e1e2e;
                border-radius: 10px;
            }
        """)
        
        # App container layout
        app_container_layout = QVBoxLayout(app_container)
        app_container_layout.setContentsMargins(0, 0, 0, 0)
        app_container_layout.setSpacing(0)
        
        # Custom title bar
        self.title_bar = TitleBar(self)
        app_container_layout.addWidget(self.title_bar)
        
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Plain)
        separator.setStyleSheet("background-color: #313244; max-height: 1px;")
        app_container_layout.addWidget(separator)
        
        # Main content container
        content_container = QWidget()
        app_container_layout.addWidget(content_container)
        
        # Apply modern dark theme
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: transparent;
                color: #cdd6f4;
            }
            QLineEdit {
                border: none;
                border-radius: 8px;
                padding: 12px;
                background-color: #313244;
                color: #cdd6f4;
                font-size: 14px;
                selection-background-color: #45475a;
            }
            QTextEdit {
                border: none;
                border-radius: 8px;
                padding: 12px;
                background-color: #313244;
                color: #cdd6f4;
                selection-background-color: #45475a;
            }
            QListWidget {
                border: none;
                border-radius: 8px;
                padding: 8px;
                background-color: #313244;
                alternate-background-color: #2a2b3c;
                color: #cdd6f4;
                outline: none;
                selection-background-color: #89b4fa;
                selection-color: #1e1e2e;
            }
            QListWidget::item {
                border-radius: 4px;
                padding: 8px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background-color: #89b4fa;
                color: #1e1e2e;
            }
            QListWidget::item:hover:!selected {
                background-color: #45475a;
            }
            QLabel {
                color: #cdd6f4;
            }
            QPushButton {
                border: none;
                border-radius: 8px;
                padding: 12px;
                background-color: #89b4fa;
                color: #1e1e2e;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #74c7ec;
            }
            QPushButton:pressed {
                background-color: #89dceb;
            }
            QPushButton:disabled {
                background-color: #45475a;
                color: #6c7086;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #313244;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #45475a;
                border-radius: 6px;
                min-height: 30px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #6c7086;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                background: none;
                border: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
                border: none;
            }
            QScrollBar:horizontal {
                border: none;
                background-color: #313244;
                height: 12px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background-color: #45475a;
                border-radius: 6px;
                min-width: 30px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #6c7086;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
                background: none;
                border: none;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
                border: none;
            }
            QScrollBar::corner {
                background: #313244;
                border: none;
            }
        """)
        
        # Container with margin
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)
        
        # Content layout
        content_container_layout = QVBoxLayout(content_container)
        content_container_layout.setContentsMargins(0, 0, 0, 0)
        content_container_layout.addWidget(container)
        
        # Add main container to the window
        main_container_layout.addWidget(app_container)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_container)
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(layout)
        
        # Header with app name and description
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 16)
        
        app_title = QLabel("WinCommander", self)
        app_title.setStyleSheet("font-size: 28px; font-weight: bold; color: #89b4fa;")
        
        app_description = QLabel("Execute powerful Windows commands with ease", self)
        app_description.setStyleSheet("font-size: 16px; color: #bac2de;")
        
        header_layout.addWidget(app_title, 0, Qt.AlignLeft)
        header_layout.addWidget(app_description, 1, Qt.AlignRight | Qt.AlignVCenter)
        
        main_layout.addWidget(header)
        
        # Main content area
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)
        
        # Left Panel - Command Browser with search
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)
        
        # Search section with icon
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 16px; color: #bac2de;")
        
        self.search_entry = QLineEdit(self)
        self.search_entry.setPlaceholderText("Search commands...")
        
        search_layout.addWidget(search_icon)
        search_layout.addWidget(self.search_entry, 1)
        
        left_layout.addWidget(search_container)
        
        # Category filter buttons
        category_container = QWidget()
        category_layout = QHBoxLayout(category_container)
        category_layout.setContentsMargins(0, 0, 0, 0)
        category_layout.setSpacing(8)
        
        self.category_buttons = {}
        categories = ["All", "System", "Network", "Maintenance", "Cleanup"]
        
        for category in categories:
            btn = QPushButton(category, self)
            btn.setCheckable(True)
            btn.setProperty("category", category.lower())
            if category == "All":
                btn.setChecked(True)
                btn.setStyleSheet("""
                    QPushButton {
                        padding: 8px 12px;
                        background-color: #89b4fa;
                        color: #1e1e2e;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        padding: 8px 12px;
                        background-color: #313244;
                        color: #cdd6f4;
                    }
                    QPushButton:checked {
                        background-color: #89b4fa;
                        color: #1e1e2e;
                    }
                """)
            btn.clicked.connect(lambda checked, cat=category: self.filter_by_category(cat))
            category_layout.addWidget(btn)
            self.category_buttons[category.lower()] = btn
        
        left_layout.addWidget(category_container)
        
        # Commands list with custom delegate
        self.listbox = QListWidget(self)
        self.listbox.setAlternatingRowColors(True)
        self.listbox.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.listbox.setStyleSheet("""
            QListWidget::item {
                padding: 12px 8px;
            }
        """)
        
        left_layout.addWidget(self.listbox, 1)
        
        # Right Panel - Command Details and Execution
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(16)
        
        # Command title and admin badge
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        self.label_title = QLabel("Select a command", self)
        self.label_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #89b4fa;")
        
        self.admin_badge = QLabel("Admin Required", self)
        self.admin_badge.setStyleSheet("""
            background-color: #f38ba8;
            color: #1e1e2e;
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 12px;
            font-weight: bold;
        """)
        self.admin_badge.hide()
        
        title_layout.addWidget(self.label_title, 1)
        title_layout.addWidget(self.admin_badge, 0)
        
        right_layout.addWidget(title_container)
        
        # Command description with syntax highlighting
        self.info_text = QTextEdit(self)
        self.info_text.setReadOnly(True)
        self.info_text.setStyleSheet("""
            font-size: 14px;
            line-height: 1.5;
        """)
        right_layout.addWidget(self.info_text, 1)
        
        # Command execution area
        execution_container = QWidget()
        execution_layout = QVBoxLayout(execution_container)
        execution_layout.setContentsMargins(0, 0, 0, 0)
        execution_layout.setSpacing(12)
        
        # Command preview with copy button
        command_preview = QWidget()
        command_preview_layout = QHBoxLayout(command_preview)
        command_preview_layout.setContentsMargins(0, 0, 0, 0)
        
        self.command_display = QLineEdit(self)
        self.command_display.setReadOnly(True)
        self.command_display.setPlaceholderText("Command will appear here")
        self.command_display.setStyleSheet("""
            background-color: #1e1e2e;
            border: 1px solid #45475a;
            font-family: 'Consolas', monospace;
        """)
        
        self.copy_button = QPushButton("Copy", self)
        self.copy_button.setIcon(QIcon.fromTheme("edit-copy"))
        self.copy_button.setCursor(Qt.PointingHandCursor)
        self.copy_button.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 4px;
                color: #cdd6f4;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45475a;
                border: 1px solid #89b4fa;
            }
            QPushButton:pressed {
                background-color: #89b4fa;
                color: #1e1e2e;
            }
        """)
        self.copy_button.clicked.connect(self.copy_command)
        
        command_preview_layout.addWidget(self.command_display, 1)
        command_preview_layout.addWidget(self.copy_button, 0)
        
        execution_layout.addWidget(command_preview)
        
        # Run button and status
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # Execute button with loading animation
        self.execute_button_container = QWidget()
        execute_button_layout = QHBoxLayout(self.execute_button_container)
        execute_button_layout.setContentsMargins(0, 0, 0, 0)
        execute_button_layout.setSpacing(8)
        
        self.execute_button = QPushButton("Execute Command", self)
        self.execute_button.setStyleSheet("""
            padding: 16px;
            font-size: 16px;
            background-color: #a6e3a1;
            color: #1e1e2e;
        """)
        
        self.loading_animation = LoadingAnimation(self)
        self.loading_animation.hide()
        
        execute_button_layout.addWidget(self.execute_button)
        execute_button_layout.addWidget(self.loading_animation)
        
        self.status_label = QLabel("", self)
        self.status_label.setStyleSheet("""
            color: #89b4fa;
            font-size: 14px;
            padding: 0 12px;
        """)
        
        button_layout.addWidget(self.execute_button_container, 1)
        button_layout.addWidget(self.status_label, 2)
        
        execution_layout.addWidget(button_container)
        
        right_layout.addWidget(execution_container)
        
        # Add panels to content
        content_layout.addWidget(left_panel, 1)
        content_layout.addWidget(right_panel, 2)
        
        main_layout.addWidget(content, 1)
        
        # Footer with version and credits
        footer = QWidget()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 12, 0, 0)
        
        version_label = QLabel("v1.0.0", self)
        version_label.setStyleSheet("color: #6c7086; font-size: 12px;")
        
        credits_label = QLabel("Made with ❤️ for Windows power users", self)
        credits_label.setStyleSheet("color: #6c7086; font-size: 12px;")
        
        footer_layout.addWidget(version_label, 0, Qt.AlignLeft)
        footer_layout.addWidget(credits_label, 0, Qt.AlignRight)
        
        main_layout.addWidget(footer)

        # Initialize data
        self.programs_info = {
            "Home Page": {
                "title": "Home Page",
                "info": "Welcome to WinCommander!\n\nSelect a command from the list to view details and execute Windows commands.",
                "command": None,
                "admin_required": False,
                "category": "all"
            }
        }

        # Load commands from online JSON
        commands = load_commands_from_json()
        if commands:
            self.programs_info.update(commands)
            logging.info(f"Successfully loaded {len(commands)} commands")
        else:
            error_msg = "Failed to load commands from online source"
            logging.error(error_msg)
            self.display_error_message(error_msg)
            # Mark the run button as failed
            self.execute_button.setText("Failed to fetch commands")
            self.execute_button.setStyleSheet("""
                QPushButton {
                    background-color: #f38ba8;
                    color: #1e1e2e;
                    padding: 16px;
                    font-size: 16px;
                }
            """)
            self.execute_button.setEnabled(False)

        # Populate the listbox with Home Page first, then other commands
        self.listbox.addItem("Home Page")
        for program in sorted(self.programs_info.keys()):
            if program != "Home Page":
                self.listbox.addItem(program)

        self.listbox.setCurrentRow(0)

        # Connect Signals and Slots
        self.listbox.currentItemChanged.connect(self.show_program_details)
        self.search_entry.textChanged.connect(self.update_listbox)
        self.execute_button.clicked.connect(self.run_command)
        self.copy_button.clicked.connect(self.copy_command)
        self.show_program_details()

        # Thread pool for running multiple scripts concurrently
        self.thread_pool = QThreadPool()
        
    def filter_by_category(self, category):
        """Filter commands by category"""
        # Update button states
        for cat, btn in self.category_buttons.items():
            if cat == category.lower():
                btn.setChecked(True)
                btn.setStyleSheet("""
                    QPushButton {
                        padding: 8px 12px;
                        background-color: #89b4fa;
                        color: #1e1e2e;
                    }
                """)
            else:
                btn.setChecked(False)
                btn.setStyleSheet("""
                    QPushButton {
                        padding: 8px 12px;
                        background-color: #313244;
                        color: #cdd6f4;
                    }
                    QPushButton:checked {
                        background-color: #89b4fa;
                        color: #1e1e2e;
                    }
                """)
        
        # Filter the list
        self.update_listbox(self.search_entry.text(), category)
    
    def copy_command(self):
        """Copy the current command to clipboard"""
        if self.command_display.text():
            # Save current button style
            original_text = self.copy_button.text()
            original_style = self.copy_button.styleSheet()
            
            # Copy to clipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(self.command_display.text())
            
            # Visual feedback - change button appearance
            self.copy_button.setText("Copied!")
            self.copy_button.setStyleSheet("""
                QPushButton {
                    padding: 8px 16px;
                    background-color: #89b4fa;
                    border: 1px solid #89b4fa;
                    border-radius: 4px;
                    color: #1e1e2e;
                    font-weight: bold;
                }
            """)
            
            # Status message
            self.status_label.setText("Command copied to clipboard")
            
            # Reset button after delay
            def reset_button():
                self.copy_button.setText(original_text)
                self.copy_button.setStyleSheet(original_style)
                self.status_label.setText("")
                
            QTimer.singleShot(2000, reset_button)
    
    def update_listbox(self, text, category="all"):
        """Update the listbox based on search text and category filter"""
        self.listbox.clear()
        
        # Always add Home Page first if we're showing all or no category filter
        if category.lower() == "all":
            self.listbox.addItem("Home Page")
        
        for program in sorted(self.programs_info.keys()):
            if program != "Home Page":
                # Check category filter
                program_category = self.programs_info[program].get('category', 'system').lower()
                if category.lower() != "all" and program_category != category.lower():
                    continue
                
                # Check search text
                if text.lower() in program.lower():
                    self.listbox.addItem(program)
        
        # Select first item if available
        if self.listbox.count() > 0:
            self.listbox.setCurrentRow(0)
        else:
            # Clear details if no items match
            self.label_title.setText("No commands found")
            self.info_text.setText("Try a different search term or category filter.")
            self.command_display.setText("")
            self.execute_button.setEnabled(False)
            self.admin_badge.hide()
            
    def show_program_details(self, item=None):
        """Display details of the selected program"""
        if item is None and self.listbox.currentItem() is None:
            return
            
        program_name = self.listbox.currentItem().text() if item is None else item.text()
        program_info = self.programs_info.get(program_name, {})
        
        # Update title and info
        self.label_title.setText(program_info.get('title', 'Unknown'))
        
        # Format the info text with some styling
        info = program_info.get('info', '')
        self.info_text.setHtml(f"""
            <div style="color: #cdd6f4; font-size: 14px; line-height: 1.5;">
                {info.replace("\n", "<br>")}
            </div>
        """)
        
        # Update command display
        cmd = program_info.get('command', '')
        if cmd:
            self.command_display.setText(cmd)
            self.execute_button.setEnabled(True)
            self.execute_button.setText("Execute Command")
            self.execute_button.setStyleSheet("""
                QPushButton {
                    padding: 16px;
                    font-size: 16px;
                    background-color: #a6e3a1;
                    color: #1e1e2e;
                }
            """)
        else:
            self.command_display.setText("")
            self.execute_button.setEnabled(False)
            
        # Show/hide admin badge
        if program_info.get('admin_required', False):
            self.admin_badge.show()
        else:
            self.admin_badge.hide()

    def display_error_message(self, message):
        error_label = QLabel(message, self)
        error_label.setStyleSheet("""
            color: #f38ba8;
            font-size: 16px;
            font-weight: bold;
            background-color: #313244;
            border-radius: 8px;
            padding: 12px;
        """)
        error_label.setGeometry(50, 50, 900, 60)
        error_label.show()
        QTimer.singleShot(5000, error_label.deleteLater)

    def center_on_screen(self):
        frame_geometry = self.frameGeometry()
        center_point = QDesktopWidget().availableGeometry().center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    def run_command(self):
        try:
            if self.is_command_running:
                return

            selected_program = self.listbox.currentItem().text()
            program_info = self.programs_info.get(selected_program)
            if not program_info or not program_info['command']:
                return

            self.is_command_running = True
            self.execute_button.setEnabled(False)
            self.execute_button.setText("Executing...")
            self.execute_button.setStyleSheet("""
                QPushButton {
                    padding: 16px;
                    font-size: 16px;
                    background-color: #74c7ec;
                    color: #1e1e2e;
                }
            """)
            self.status_label.setText("Command is running...")
            self.loading_animation.start_animation()

            command = program_info['command']
            admin_required = program_info['admin_required']

            runnable = CommandRunner(command, admin_required)
            runnable.signals.finished.connect(self.command_finished)
            runnable.signals.error.connect(self.command_error)
            
            self.thread_pool.start(runnable)
            logging.info("Started command execution: {}".format(command))
        except Exception as e:
            error_msg = f"Error initiating command: {e}"
            logging.error(error_msg)
            self.command_error(error_msg)

    def command_finished(self):
        self.is_command_running = False
        self.execute_button.setEnabled(True)
        self.execute_button.setText("Execute Command")
        self.execute_button.setStyleSheet("""
            QPushButton {
                padding: 16px;
                font-size: 16px;
                background-color: #a6e3a1;
                color: #1e1e2e;
            }
        """)
        self.status_label.setText("Command executed successfully")
        self.loading_animation.stop_animation()
        
        # Clear status after 2 seconds
        QTimer.singleShot(2000, lambda: self.status_label.setText(""))
        
        logging.info("Command execution completed")

    def command_error(self, error_msg):
        self.display_error_message(error_msg)
        self.is_command_running = False
        self.execute_button.setEnabled(True)
        self.execute_button.setText("Execute Command")
        self.execute_button.setStyleSheet("""
            QPushButton {
                padding: 16px;
                font-size: 16px;
                background-color: #a6e3a1;
                color: #1e1e2e;
            }
        """)
        self.status_label.setText("Command failed")
        self.loading_animation.stop_animation()
        
        # Clear status after 2 seconds
        QTimer.singleShot(2000, lambda: self.status_label.setText(""))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())