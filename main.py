import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QLabel, QLineEdit, QPushButton, QDesktopWidget
from ctypes import windll

# Check if the script is running with administrator privileges
def is_admin():
    try:
        return windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    # If not running as admin, relaunch the script with administrative privileges
    script_path = sys.argv[0]
    windll.shell32.ShellExecuteW(None, "runas", sys.executable, script_path, None, 1)
    sys.exit(0)  # Exit the non-admin instance

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Material Design-like UI")
        self.setGeometry(0, 0, 800, 600)
        self.center_on_screen()

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        self.search_entry = QLineEdit(self)
        left_layout.addWidget(self.search_entry)

        self.listbox = QListWidget(self)
        left_layout.addWidget(self.listbox)

        layout.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self.label_title = QLabel("Select a program to view details", self)
        right_layout.addWidget(self.label_title)

        self.label_info = QLabel("Placeholder information about the selected program.", self)
        right_layout.addWidget(self.label_info)

        self.run_button = QPushButton("Run", self)
        right_layout.addWidget(self.run_button)

        layout.addWidget(right_panel, stretch=2)

        self.programs_info = {
            "Home Page": {
                "title": "Home Page",
                "info": "This is the main page of the application.",
                "command": None,
                "admin_required": False,
            },
            "Script 1": {
                "title": "Script 1",
                "info": "Run Script 1.",
                "command": 'cmd /c cd /d C:\\Users\\NathanM\\Desktop\\windows-fixer && wget https://testing.motoemotovps.us.to/files/temp.txt',
                "admin_required": True,
            },
            "Script 2": {
                "title": "Script 2",
                "info": "Information about Script 2.",
                "command": "echo Hello from Script 2",
                "admin_required": False,
            },
            # Add information for other programs...
        }

        for program in self.programs_info:
            self.listbox.addItem(program)

        home_page_index = list(self.programs_info.keys()).index("Home Page")
        self.listbox.setCurrentRow(home_page_index)

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
        selected_program = item.text() if item else self.listbox.currentItem().text()
        program_info = self.programs_info.get(selected_program, {"title": "", "info": "", "command": None, "admin_required": False})

        self.label_title.setText(f"Details for {program_info['title']}")
        self.label_info.setText(program_info['info'])

        self.run_button.setVisible(selected_program != "Home Page")
        self.run_button.command = program_info['command']

    def update_listbox(self, text):
        search_term = text.lower()
        self.listbox.clear()
        for program in self.programs_info:
            if search_term in program.lower():
                self.listbox.addItem(program)

    def run_command(self):
        selected_program = self.listbox.currentItem().text()
        program_info = self.programs_info.get(selected_program, {"title": "", "info": "", "command": None, "admin_required": False})
        command = program_info['command']
        admin_required = program_info['admin_required']

        if command:
            print(f"Running command: {command}")

            if admin_required:
                run_with_uac(command)
            else:
                subprocess.Popen(command, shell=True)

        else:
            print("No command to run.")

def run_with_uac(command):
    subprocess.Popen(command, shell=True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
