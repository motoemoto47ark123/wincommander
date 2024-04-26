import sys
import subprocess
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QLabel, QLineEdit, QPushButton, QDesktopWidget, QTextEdit
from PyQt5.QtGui import QFont, QColor
from ctypes import windll
from PyQt5.QtCore import QTimer, QThreadPool, QRunnable
import psycopg2
from psycopg2 import OperationalError, extras
import os

# Setup logging
log_directory = os.path.join("C:", os.sep, "Users", "Public", "Documents", "wincommander")
if not os.path.exists(log_directory):
    os.makedirs(log_directory)
log_filename = os.path.join(log_directory, 'wincommander.log')
logging.basicConfig(filename=log_filename, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Database connection details
DB_CONNECTION_STRING = ""

# Check if the script is running with administrator privileges
def is_admin():
    try:
        result = windll.shell32.IsUserAnAdmin()
        logging.info("Checked for administrator privileges: Admin={}".format(result))
        return result
    except Exception as e:
        logging.error("Error checking administrator privileges: {}".format(e))
        return False

if not is_admin():
    # If not running as admin, relaunch the script with administrative privileges
    script_path = sys.argv[0]
    try:
        windll.shell32.ShellExecuteW(None, "runas", sys.executable, script_path, None, 1)
        logging.info("Relaunched script with admin privileges.")
    except Exception as e:
        logging.error("Error relaunching as admin: {}".format(e))
    sys.exit(0)  # Exit the non-admin instance

def create_database_connection():
    """Create a database connection to the PostgreSQL server."""
    connection = None
    try:
        connection = psycopg2.connect(DB_CONNECTION_STRING)
        logging.info("PostgreSQL Database connection successful")
    except OperationalError as e:
        logging.error("Error connecting to PostgreSQL Database: {}".format(e))
    return connection

def fetch_programs_info(connection):
    """Fetch programs information from the database."""
    cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    query = "SELECT name, title, info, command, admin_required FROM scripts"
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        logging.info("Fetched programs information successfully")
        return {item['name']: item for item in result}
    except (OperationalError, psycopg2.Error) as e:
        logging.error("Error fetching data from PostgreSQL table: {}".format(e))
        return {}

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()

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
        left_layout.addWidget(self.search_entry)

        self.listbox = QListWidget(self)
        # Increase the font size of the listbox items and make them unbold
        font = self.listbox.font()
        font.setPointSize(14)  # Set the font size to 14
        font.setBold(False)  # Make the font unbold
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
        # Increase the font size of the text
        font = self.info_text.font()
        font.setPointSize(14)  # Set the font size to 14
        self.info_text.setFont(font)
        right_layout.addWidget(self.info_text)

        self.run_button = QPushButton("Run", self)
        # Increase the font size of the run button text and change the color of the run button to green
        font = self.run_button.font()
        font.setPointSize(18)  # Set the font size to 18
        self.run_button.setFont(font)
        self.run_button.setStyleSheet("background-color: green")
        right_layout.addWidget(self.run_button)

        layout.addWidget(right_panel, stretch=2)

        # Fetch and display program information from the database
        connection = create_database_connection()
        if connection:
            self.programs_info = fetch_programs_info(connection)
            connection.close()
        else:
            self.programs_info = {}
            logging.error("Failed to create database connection.")
            self.display_error_message("Failed to connect to the database or fetch information.")

        for program in self.programs_info:
            self.listbox.addItem(program)
        if self.programs_info:
            home_page_index = list(self.programs_info.keys()).index("Home Page")
            self.listbox.setCurrentRow(home_page_index)

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
            self.info_text.setPlainText(program_info['info'])

            self.run_button.setVisible(selected_program != "Home Page")
            self.run_button.command = program_info['command']
            logging.info("Displayed program details for: {}".format(selected_program))
        except Exception as e:
            logging.error("Error showing program details: {}".format(e))

    def update_listbox(self, text):
        try:
            search_term = text.lower()
            self.listbox.clear()

            for program, program_info in self.programs_info.items():
                if search_term in program.lower():
                    self.listbox.addItem(program)
            logging.info("Updated listbox with search term: {}".format(text))
        except Exception as e:
            logging.error("Error updating listbox: {}".format(e))

    def run_command(self):
        try:
            selected_program = self.listbox.currentItem().text()
            program_info = self.programs_info.get(selected_program, {"title": "", "info": "", "command": None, "admin_required": False})
            command = program_info['command']
            admin_required = program_info['admin_required']

            if command:
                logging.info("Running command: {}".format(command))
                self.run_button.setText("Running...")
                runnable = CommandRunner(command, admin_required)
                self.thread_pool.start(runnable)
                QTimer.singleShot(17000, lambda: self.run_button.setText("Run"))

            else:
                logging.info("No command to run.")
        except Exception as e:
            logging.error("Error running command: {}".format(e))

class CommandRunner(QRunnable):
    def __init__(self, command, admin_required):
        super().__init__()
        self.command = command
        self.admin_required = admin_required

    def run(self):
        if self.admin_required:
            run_with_uac(self.command)
        else:
            subprocess.Popen(self.command, shell=True)
        logging.info("Executed command: {}".format(self.command))

def run_with_uac(command):
    subprocess.Popen(command, shell=True)
    logging.info("Executed command with UAC: {}".format(command))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())