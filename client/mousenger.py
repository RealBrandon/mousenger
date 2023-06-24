# Mousenger v0.2
# Mousenger, a chat program with client and server both written in Python
# Brandon Han
# 24 Jun 2023
# This is an entry point for the Mousenger client.

from controller import Controller
from model import Model
from ui.main_window import MainWindow
from ui.login_window import LoginWindow

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

app = QApplication(sys.argv)
app.setWindowIcon(QIcon("./ui/happy_mouse.webp"))
model = Model()
main_window = MainWindow()
login_window = LoginWindow()
controller = Controller()
sys.exit(app.exec())

