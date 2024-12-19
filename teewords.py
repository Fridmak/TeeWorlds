import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from start_info_handler import InputWindow
from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = InputWindow()
    window.show()

    sys.exit(app.exec_())