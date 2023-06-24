from PyQt6 import QtGui, QtCore, QtWidgets

if __name__ == '__main__':
    from colour import *
else:
    from ui.colour import *


class LoginWindow(QtWidgets.QDialog):

    def __init__(self):
        super().__init__()
        self.__init_ui()

    def __init_ui(self):
        self.setWindowTitle('Login')
        self.setFixedSize(500, 400)
        self.setStyleSheet(f'background-color:{MAIN_COLOUR};')

        ver_spacer = QtWidgets.QSpacerItem(20, 20,
                                           QtWidgets.QSizePolicy.Policy.Minimum,
                                           QtWidgets.QSizePolicy.Policy.Expanding)
        hor_spacer = QtWidgets.QSpacerItem(20, 20,
                                           QtWidgets.QSizePolicy.Policy.Expanding,
                                           QtWidgets.QSizePolicy.Policy.Minimum)

        master_layout = QtWidgets.QVBoxLayout()
        master_layout.addSpacerItem(ver_spacer)

        banner_layout = QtWidgets.QHBoxLayout()
        banner_layout.addSpacerItem(hor_spacer)
        banner_icon_label = QtWidgets.QLabel(self)
        if __name__ == "__main__":
            # Set banner icon picture when this is the main program.
            banner_icon_label.setPixmap(QtGui.QPixmap("happy_mouse.webp"))
        else:
            # Set banner icon picture when this is a module.
            banner_icon_label.setPixmap(QtGui.QPixmap('./ui/happy_mouse.webp'))
        banner_icon_label.setScaledContents(True)
        banner_icon_label.setFixedHeight(int(self.height() * 0.3))
        banner_icon_label.setFixedWidth(banner_icon_label.height())
        banner_layout.addWidget(banner_icon_label)
        banner_text_label = QtWidgets.QLabel('Mousenger', self)
        banner_text_label.setStyleSheet(f'color:{MAIN_COLOUR_LIGHTEST};')
        font = QtGui.QFont()
        font.setPointSize(30)
        font.setBold(True)
        banner_text_label.setFont(font)
        banner_layout.addWidget(banner_text_label)
        banner_layout.addSpacerItem(hor_spacer)
        master_layout.addLayout(banner_layout)

        master_layout.addSpacerItem(ver_spacer)
        central_layout = QtWidgets.QHBoxLayout()

        label_layout = QtWidgets.QVBoxLayout()
        username_label = QtWidgets.QLabel('Username:', self)
        username_label.setStyleSheet('color:white;')
        font = QtGui.QFont()
        font.setPointSize(13)
        username_label.setFont(font)
        label_layout.addWidget(username_label)
        password_label = QtWidgets.QLabel('Password:', self)
        password_label.setStyleSheet('color:white;')
        password_label.setFont(font)
        label_layout.addWidget(password_label)
        central_layout.addLayout(label_layout)

        line_edit_layout = QtWidgets.QVBoxLayout()
        self.__username_edit = QtWidgets.QLineEdit(self)
        self.__username_edit.setStyleSheet(
            f'background-color:{MAIN_COLOUR_LIGHT};'
            'color:white;'
        )
        line_edit_layout.addWidget(self.__username_edit)
        self.__password_edit = QtWidgets.QLineEdit(self)
        self.__password_edit.setStyleSheet(
            f'background-color:{MAIN_COLOUR_LIGHT};'
            'color:white;'
        )
        self.__password_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        line_edit_layout.addWidget(self.__password_edit)
        central_layout.addLayout(line_edit_layout)

        master_layout.addLayout(central_layout)
        master_layout.addSpacerItem(ver_spacer)

        self.__info_label = QtWidgets.QLabel(self)
        self.__info_label.setStyleSheet('color:white;')
        font = QtGui.QFont('Serif', 15, 700, True)
        self.__info_label.setFont(font)
        master_layout.addWidget(self.__info_label)

        master_layout.addSpacerItem(ver_spacer)

        button_layout = QtWidgets.QHBoxLayout()
        self.login_button = QtWidgets.QPushButton('Login', self)
        self.login_button.setStyleSheet(
            f'background-color:{MAIN_COLOUR_LIGHTER};'
            'color:white;'
        )
        font = QtGui.QFont()
        font.setPointSize(13)
        self.login_button.setFont(font)
        button_layout.addWidget(self.login_button)
        self.exit_button = QtWidgets.QPushButton('Exit', self)
        self.exit_button.setStyleSheet(
            f'background-color:{MAIN_COLOUR_LIGHTER};'
            'color:white;'
        )
        self.exit_button.setFont(font)
        button_layout.addWidget(self.exit_button)
        master_layout.addLayout(button_layout)

        self.setLayout(master_layout)

    def get_user_input(self) -> tuple:
        username = self.__username_edit.text()
        password = self.__password_edit.text()
        return username, password

    def set_prompt_text(self, text: str):
        self.__info_label.setText(text)


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    login_dialogue = LoginWindow()
    login_dialogue.open()
    sys.exit(app.exec())
