import socket
import sys, os, subprocess
import threading
import time

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from scripts import settings


class InputWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('IP и Порт ввод')

        layout = QVBoxLayout()

        self.ip_label = QLabel('IP:')
        self.ip_input = QLineEdit()
        self.ip_input.setText(settings.HOST)
        layout.addWidget(self.ip_label)
        layout.addWidget(self.ip_input)

        self.port_label = QLabel('Порт:')
        self.port_input = QLineEdit()
        self.port_input.setText(str(settings.PORT))
        layout.addWidget(self.port_label)
        layout.addWidget(self.port_input)

        self.start_button = QPushButton('Начать')
        self.start_button.clicked.connect(self.on_start)
        layout.addWidget(self.start_button)

        self.setLayout(layout)

    def on_start(self):
        self.host = self.ip_input.text()
        self.port = int(self.port_input.text())
        settings.HOST = self.host
        settings.PORT = self.port

        self.start_game()

    def start_game(self):
        if not self.is_server_running():
            thread = threading.Thread(target=self._run_backend_scripts, args=('server.py',))
            thread.start()

        self.close()
        time.sleep(0.3)
        self._run_backend_scripts('game.py')

    def _run_backend_scripts(self, file):
        base_directory = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        script_path = os.path.join(base_directory, 'backend', file)
        python_executable = sys.executable

        subprocess.run([python_executable, script_path])

    def is_server_running(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)

            result = sock.connect_ex((self.host, self.port))

            return result == 0
        except socket.error:
            return False
        finally:
            sock.close()
