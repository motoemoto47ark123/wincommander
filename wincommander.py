import sys
import subprocess
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QLabel, QLineEdit, QPushButton, QDesktopWidget, QTextEdit
from PyQt5.QtGui import QFont, QColor
from ctypes import windll
from PyQt5.QtCore import QTimer, QThreadPool, QRunnable, pyqtSignal, QObject
import os
import json

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
    """Load commands from the JSON file."""
    try:
        with open('windows_commands.json', 'r') as file:
            data = json.load(file)
            commands = data.get('commands', [])
            return {cmd['name']: {
                'title': cmd['name'],
                'info': cmd['description'] + "\n\n" + cmd['notes'],
                'command': cmd['command'],
                'admin_required': cmd['admin_required']
            } for cmd in commands}
    except Exception as e:
        logging.error(f"Error loading commands from JSON: {e}")
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
                run_as_admin(self.command)
            else:
                subprocess.Popen(self.command, shell=True)
            logging.info(f"Executed command: {self.command} (admin_required: {self.admin_required})")
        except Exception as e:
            error_msg = f"Error executing command: {e}"
            logging.error(error_msg)
            self.signals.error.emit(error_msg)
        finally:
            self.signals.finished.emit()

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_command_running = False
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("wincommander")
        self.setGeometry(0, 0, 800, 600)
        self.center_on_screen()

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)

        # Left Panel
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        self.search_entry = QLineEdit(self)
        self.search_entry.setPlaceholderText("Search commands...")
        left_layout.addWidget(self.search_entry)

        self.listbox = QListWidget(self)
        # Increase the font size of the listbox items and make them unbold
        font = self.listbox.font()
        font.setPointSize(14)
        font.setBold(False)
        self.listbox.setFont(font)
        left_layout.addWidget(self.listbox)

        layout.addWidget(left_panel)

        # Right Panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self.label_title = QLabel("Select a program to view details", self)
        right_layout.addWidget(self.label_title)

        self.info_text = QTextEdit(self)
        self.info_text.setReadOnly(True)
        font = self.info_text.font()
        font.setPointSize(14)
        self.info_text.setFont(font)
        right_layout.addWidget(self.info_text)

        # Button container for better layout control
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        
        self.run_button = QPushButton("Run", self)
        font = self.run_button.font()
        font.setPointSize(18)
        self.run_button.setFont(font)
        self.run_button.setStyleSheet("QPushButton { background-color: green; color: white; padding: 10px; border-radius: 5px; } QPushButton:disabled { background-color: gray; }")
        button_layout.addWidget(self.run_button)
        
        self.status_label = QLabel("", self)
        self.status_label.setStyleSheet("color: blue; font-size: 14px;")
        button_layout.addWidget(self.status_label)
        
        right_layout.addWidget(button_container)

        layout.addWidget(right_panel, stretch=2)

        # Add a home page entry first
        self.programs_info = {
            "Home Page": {
                "title": "Home Page",
                "info": "Welcome to wincommander!\n\nSelect a command from the list to view details and execute Windows commands.",
                "command": None,
                "admin_required": False
            }
        }

        # Load commands from JSON file
        try:
            with open('windows_commands.json', 'r') as file:
                data = json.load(file)
                commands = data.get('commands', [])
                # Sort commands by name for consistent ordering
                commands.sort(key=lambda x: x['name'])
                for cmd in commands:
                    self.programs_info[cmd['name']] = {
                        'title': cmd['name'],
                        'info': cmd['description'] + "\n\n" + cmd['notes'],
                        'command': cmd['command'],
                        'admin_required': cmd['admin_required']
                    }
                logging.info(f"Successfully loaded {len(commands)} commands from JSON file")
        except Exception as e:
            error_msg = f"Error loading commands from JSON file: {e}"
            logging.error(error_msg)
            self.display_error_message(error_msg)

        # Populate the listbox with Home Page first, then other commands
        self.listbox.addItem("Home Page")
        for program in sorted(self.programs_info.keys()):
            if program != "Home Page":
                self.listbox.addItem(program)

        self.listbox.setCurrentRow(0)

        # Connect Signals and Slots
        self.listbox.currentItemChanged.connect(self.show_program_details)
        self.search_entry.textChanged.connect(self.update_listbox)
        self.run_button.clicked.connect(self.run_command)
        self.show_program_details()

        # Thread pool for running multiple scripts concurrently
        self.thread_pool = QThreadPool()

    def display_error_message(self, message):
        error_label = QLabel(message, self)
        error_label.setStyleSheet("color: red; font-size: 20px; font-weight: bold;")
        error_label.setGeometry(10, 10, 780, 40)
        error_label.show()
        QTimer.singleShot(5000, error_label.deleteLater)

    def center_on_screen(self):
        frame_geometry = self.frameGeometry()
        center_point = QDesktopWidget().availableGeometry().center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    def show_program_details(self, item=None):
        try:
            selected_program = item.text() if item and hasattr(item, 'text') else self.listbox.currentItem().text()
            program_info = self.programs_info.get(selected_program, {"title": "", "info": "", "command": None, "admin_required": False})

            self.label_title.setText(f"{program_info['title']}")
            info_text = program_info['info']
            if program_info['admin_required']:
                info_text += "\n\n[This command requires administrator privileges]"
            self.info_text.setPlainText(info_text)

            # Only show run button if there's a command and we're not on the home page
            self.run_button.setVisible(bool(program_info['command']) and selected_program != "Home Page")
            self.run_button.setEnabled(not self.is_command_running)
            self.run_button.command = program_info['command']
            self.run_button.admin_required = program_info['admin_required']
            
            logging.info("Displayed program details for: {}".format(selected_program))
        except Exception as e:
            logging.error("Error showing program details: {}".format(e))

    def update_listbox(self, text):
        try:
            search_term = text.lower()
            self.listbox.clear()

            # Always add Home Page first if it matches the search
            if "home page".startswith(search_term):
                self.listbox.addItem("Home Page")

            # Then add other matching items
            for program in sorted(self.programs_info.keys()):
                if program != "Home Page" and search_term in program.lower():
                    self.listbox.addItem(program)
            
            logging.info("Updated listbox with search term: {}".format(text))
        except Exception as e:
            logging.error("Error updating listbox: {}".format(e))

    def command_finished(self):
        self.is_command_running = False
        self.run_button.setEnabled(True)
        self.run_button.setText("Run")
        self.status_label.clear()
        logging.info("Command execution completed")

    def command_error(self, error_msg):
        self.display_error_message(error_msg)
        self.command_finished()

    def run_command(self):
        try:
            if self.is_command_running:
                return

            selected_program = self.listbox.currentItem().text()
            program_info = self.programs_info.get(selected_program)
            if not program_info or not program_info['command']:
                return

            self.is_command_running = True
            self.run_button.setEnabled(False)
            self.run_button.setText("Running...")
            self.status_label.setText("Command is running...")

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())