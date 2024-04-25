import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QLabel, QLineEdit, QPushButton, QDesktopWidget, QTextEdit
from PyQt5.QtGui import QFont, QColor
from ctypes import windll
from PyQt5.QtCore import QTimer, QThreadPool, QRunnable
import mysql.connector
from mysql.connector import Error

# Database connection details
DB_HOST = ""
DB_USER = ""
DB_PASSWORD = ""
DB_NAME = ""
DB_PORT = 3305

# Check if the script is running with administrator privileges
def is_admin():
    try:
        return windll.shell32.IsUserAnAdmin()
    except Exception as e:
        print(f"Error checking administrator privileges: {e}")
        return False

if not is_admin():
    # If not running as admin, relaunch the script with administrative privileges
    script_path = sys.argv[0]
    try:
        windll.shell32.ShellExecuteW(None, "runas", sys.executable, script_path, None, 1)
    except Exception as e:
        print(f"Error relaunching as admin: {e}")
    sys.exit(0)  # Exit the non-admin instance

def create_database_connection():
    """Create a database connection to the MySQL server."""
    connection = None
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            passwd=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT
        )
        print("MySQL Database connection successful")
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

def fetch_programs_info(connection):
    """Fetch programs information from the database."""
    cursor = connection.cursor(dictionary=True)
    query = "SELECT name, title, info, command, admin_required FROM scripts"
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return {item['name']: item for item in result}
    except Error as e:
        print(f"Error fetching data from MySQL table: {e}")
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

        for program in self.programs_info:
            self.listbox.addItem(program)
        home_page_index = list(self.programs_info.keys()).index("Home Page")
        self.listbox.setCurrentRow(home_page_index)

        # Connect Signals and Slots
        self.listbox.currentItemChanged.connect(self.show_program_details)
        self.search_entry.textChanged.connect(self.update_listbox)
        self.run_button.clicked.connect(self.run_command)
        self.show_program_details()

        # Thread pool for running multiple scripts concurrently
        self.thread_pool = QThreadPool()

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
        except Exception as e:
            print(f"Error showing program details: {e}")

    def update_listbox(self, text):
        try:
            search_term = text.lower()
            self.listbox.clear()

            for program, program_info in self.programs_info.items():
                if search_term in program.lower():
                    self.listbox.addItem(program)
        except Exception as e:
            print(f"Error updating listbox: {e}")

    def run_command(self):
        try:
            selected_program = self.listbox.currentItem().text()
            program_info = self.programs_info.get(selected_program, {"title": "", "info": "", "command": None, "admin_required": False})
            command = program_info['command']
            admin_required = program_info['admin_required']

            if command:
                print(f"Running command: {command}")
                self.run_button.setText("Running...")
                runnable = CommandRunner(command, admin_required)
                self.thread_pool.start(runnable)
                QTimer.singleShot(17000, lambda: self.run_button.setText("Run"))

            else:
                print("No command to run.")
        except Exception as e:
            print(f"Error running command: {e}")

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

def run_with_uac(command):
    subprocess.Popen(command, shell=True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())