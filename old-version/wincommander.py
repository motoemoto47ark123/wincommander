import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QLabel, QLineEdit, QPushButton, QDesktopWidget, QTextEdit
from PyQt5.QtGui import QFont, QColor
from ctypes import windll
from PyQt5.QtCore import QTimer

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

        # Program Information
        self.programs_info = {
            "Home Page": {
                "title": "",
                "info": "Welcome to wincommander! This application helps you run various items on the list to fix common issues on Windows.\n\n"
                        "Use the left panel to search for a specific item or select one from the list. The right panel displays details about the selected item, and you can run it by clicking the 'Run' button.\n\n"
                        "Remember, not all Windows problems are the same. If one item doesn't work, try another one. We've included multiple items for some common issues to give you more options. For example, if the 'Reset audio' item doesn't work, you can try the 'Reset audio 2' item.\n\n"
                        "Make sure to select the item that best matches your problem. If you're having audio issues, try one of the audio items. If you're unsure, don't worry! Just give it a try and see if it helps.\n\n"
                        "This tool is designed to be user-friendly, even for those who are not very tech-savvy. So don't worry if you're not a computer expert - we've got you covered! If you're still having trouble, feel free to email us or visit our website at wincommander.us.to for more help.\n\n"
                        "Feel free to explore and enhance your Windows experience with wincommander!",
                "command": None,
                "admin_required": False,
            },
            "windows-search-reset": {
                "title": "",
                "info": "This script restarts Windows Explorer.\n\n"
                        "Command: `taskkill /f /im explorer.exe && start explorer.exe`\n\n"
                        "Administrator Privileges: Required",
                "command": 'taskkill /f /im explorer.exe && start explorer.exe',
                "admin_required": True,
            },
            "Restart Internet Service": {
                "title": "",
                "info": "This script restarts the Internet service to fix common Internet issues in Windows.\n\n"
                        "Command: `net stop wuauserv && net start wuauserv`\n\n"
                        "Administrator Privileges: Required",
                "command": "net stop wuauserv && net start wuauserv",
                "admin_required": True,
            },
            "Reset audio": {
                "title": "",
                "info": "This script fixes sound problems. It turns off and then turns on the sound services.\n\n"
                        "Command: `net stop audiosrv && net stop AudioEndpointBuilder && net start audiosrv && net start AudioEndpointBuilder`\n\n"
                        "Administrator Privileges: Required",
                "command": "net stop audiosrv && net stop AudioEndpointBuilder && net start audiosrv && net start AudioEndpointBuilder",
                "admin_required": True,
            },
            "Reset audio 2": {
                "title": "",
                "info": "This is another script to fix sound problems. If 'Reset audio' didn't work, try this one. It just starts the sound services without turning them off first.\n\n"
                        "Command: `net start audiosrv && net start AudioEndpointBuilder`\n\n"
                        "Administrator Privileges: Required",
                "command": "net start audiosrv && net start AudioEndpointBuilder",
                "admin_required": True,
            },
            
            # Add information for other programs...
        }

        for program in self.programs_info:
            self.listbox.addItem(program)
        home_page_index = list(self.programs_info.keys()).index("Home Page")
        self.listbox.setCurrentRow(home_page_index)

        # Connect Signals and Slots
        self.listbox.currentItemChanged.connect(self.show_program_details)
        self.search_entry.textChanged.connect(self.update_listbox)
        self.run_button.clicked.connect(self.run_command)
        self.show_program_details()

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
                QTimer.singleShot(12000, lambda: self.run_button.setText("Script is done running."))
                QTimer.singleShot(17000, lambda: self.run_button.setText("Run"))
                if admin_required:
                    run_with_uac(command)
                else:
                    subprocess.Popen(command, shell=True)

            else:
                print("No command to run.")
        except Exception as e:
            print(f"Error running command: {e}")

def run_with_uac(command):
    subprocess.Popen(command, shell=True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())


