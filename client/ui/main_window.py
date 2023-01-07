from PyQt6 import QtGui, QtCore, QtWidgets
from model import Model

if __name__ == '__main__':
    from colour import *
else:
    from ui.colour import *


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, model: Model):
        super().__init__()
        self.__model = model
        self.__init_ui()

    def __init_ui(self):
        self.setWindowTitle('Mousenger')
        self.setMinimumSize(800, 700)
        self.__create_menu_bar()

        central_widget = QtWidgets.QWidget(self)
        central_widget.setStyleSheet(f'background-color:{MAIN_COLOUR};')
        outermost_layout = QtWidgets.QHBoxLayout()

        chat_list_layout = QtWidgets.QVBoxLayout()
        chat_list_layout.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetMaximumSize)
        chat_list_width = int(self.width() / 3)
        self.search_bar = QtWidgets.QLineEdit(self)
        self.search_bar.setPlaceholderText('Search by username')
        self.search_bar.setStyleSheet(
            f'background-color:{MAIN_COLOUR_LIGHT};'
            'color:white;'
        )
        self.search_bar.setMaximumWidth(chat_list_width)
        chat_list_layout.addWidget(self.search_bar)
        self.chat_list = QtWidgets.QListWidget(self)
        self.chat_list.setStyleSheet(
            f'background-color:{MAIN_COLOUR_LIGHT};'
            'color:white;'
        )
        self.chat_list.setMaximumWidth(chat_list_width)
        font = QtGui.QFont()
        font.setPointSize(15)
        font.setBold(True)
        self.chat_list.setFont(font)
        chat_list_layout.addWidget(self.chat_list)
        self.__status_label = QtWidgets.QLabel(self)
        self.setStyleSheet('color:white;')
        font = QtGui.QFont('Serif', 15, 700, True)
        self.__status_label.setFont(font)
        self.__status_label.setMaximumWidth(chat_list_width)
        chat_list_layout.addWidget(self.__status_label)
        outermost_layout.addLayout(chat_list_layout)

        chat_main_layout = QtWidgets.QVBoxLayout()

        chat_title_layout = QtWidgets.QHBoxLayout()
        self.__chat_title_label = QtWidgets.QLabel(self)
        self.__chat_title_label.setStyleSheet('color:white;')
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.__chat_title_label.setFont(font)
        chat_title_layout.addWidget(self.__chat_title_label)
        self.__online_status_label = QtWidgets.QLabel(self)
        self.__online_status_label.setStyleSheet('color:white;')
        font.setPointSize(12)
        font.setBold(False)
        self.__online_status_label.setFont(font)
        chat_title_layout.addWidget(self.__online_status_label)
        horizontal_spacer = QtWidgets.QSpacerItem(20, 20,
                                                  QtWidgets.QSizePolicy.Policy.Expanding,
                                                  QtWidgets.QSizePolicy.Policy.Minimum)
        chat_title_layout.addSpacerItem(horizontal_spacer)
        chat_main_layout.addLayout(chat_title_layout)

        self.__chat_display = QtWidgets.QTextBrowser(self)
        self.__chat_display.setLineWrapMode(
            QtWidgets.QTextBrowser.LineWrapMode.WidgetWidth
        )
        chat_main_layout.addWidget(self.__chat_display)

        type_area_layout = QtWidgets.QHBoxLayout()
        self.msg_edit = QtWidgets.QLineEdit(self)
        self.msg_edit.setStyleSheet(
            f'background-color:{MAIN_COLOUR_LIGHT};'
            'color:white;'
        )
        type_area_layout.addWidget(self.msg_edit)
        self.send_button = QtWidgets.QPushButton('Send', self)
        self.send_button.setStyleSheet(f'background-color:{MAIN_COLOUR_LIGHTER};')
        type_area_layout.addWidget(self.send_button)
        chat_main_layout.addLayout(type_area_layout)

        outermost_layout.addLayout(chat_main_layout)

        central_widget.setLayout(outermost_layout)
        self.setCentralWidget(central_widget)

    def __create_menu_bar(self):
        menu_bar = self.menuBar()
        menu_bar.setStyleSheet(
            f'background-color:{MAIN_COLOUR_LIGHT};'
            f'color:{FONT_COLOUR1};'
        )
        font = QtGui.QFont()
        font.setPointSize(12)
        menu_bar.setFont(font)

        self.exit_action = QtGui.QAction('&Exit', self)
        menu_bar.addAction(self.exit_action)
        about_action = QtGui.QAction('&About', self)
        menu_bar.addAction(about_action)

    def get_search_bar_input(self) -> str:
        query = self.search_bar.text()
        return query

    def set_chat_list(self, data: list = None):
        '''Default to using the chat list stored in model'''
        if data is None:
            data = self.__model.get_chat_list()

        current_title = self.__model.get_cur_chat_title()
        self.chat_list.clear()
        for chat_title in data:
            item = QtWidgets.QListWidgetItem(chat_title)
            if chat_title == current_title:
                colour = QtGui.QColor(64, 128, 191)  # MAIN_COLOUR_LIGHTEST
                item.setBackground(colour)
            self.chat_list.addItem(item)

    def get_activated_chat_title(self) -> str:
        chat_title = self.chat_list.currentItem().text()
        return chat_title

    # def set_chat_top(self, is_online: bool):
    #     self.__chat_title_label.setText(self.__model.get_current_chat_title())
    #     if is_online:
    #         self.__online_status_label.setText('online')
    #     else:
    #         self.__online_status_label.setText('offline')

    def set_chat_top(self):
        self.__chat_title_label.setText(self.__model.get_cur_chat_title())

    def update_chat_display(self):
        ver_scroll_bar = self.__chat_display.verticalScrollBar()
        prev_scroll = ver_scroll_bar.sliderPosition()
        prev_max_scroll = ver_scroll_bar.maximum()
        ver_scroll_bar.setSliderDown(True)

        chat_history = self.__model.get_msg()
        content = ''
        for sender, message in chat_history:
            if sender == 'You':
                content += '<b>'
            else:
                content += f'<b style="color:{MAIN_COLOUR_LIGHTEST};">'
            content += f'{sender}</b>' + '<br>'
            content += message + '<br>'
            content += '<br>'
        self.__chat_display.setHtml(content)

        new_max_scroll = ver_scroll_bar.maximum()
        if prev_max_scroll == 0:
            # If previous_max_scroll is 0,
            # the previous screen was too short to scroll,
            # so the equivalent for now is maximum scroll.
            equiv_scroll = new_max_scroll
        else:
            # Use the prev_scroll/prev_max_scroll ratio to calculate
            # the equivalent under new_max_scroll.
            equiv_scroll = int(prev_scroll / prev_max_scroll * new_max_scroll)

        if new_max_scroll - equiv_scroll <= 230:
            # If less than 230 px,
            # then it was near/at the end before,
            # so scroll to the end.
            ver_scroll_bar.setValue(new_max_scroll)
        else:
            ver_scroll_bar.setValue(equiv_scroll)

    def set_type_area_visibility(self, set_visible: bool):
        '''Set visibility of msg_edit and send_button.'''
        self.msg_edit.setVisible(set_visible)
        if set_visible:  # Set focus on msg_edit if it's set visible.
            self.msg_edit.setFocus()
        self.send_button.setVisible(set_visible)

    def get_msg_edit_input(self) -> str:
        message = self.msg_edit.text()
        return message

    def clear_msg_edit(self):
        self.msg_edit.clear()
        self.msg_edit.setFocus()

    # def adjust_msg_edit_height(self):
    #     '''Adjust the height of msg_edit to fit its content.'''
    #     max_height = 262
    #     doc_height = self.msg_edit.document().size().height()
    #     padding: int = 2
    #     new_height = int(doc_height) + padding
    #     if new_height > max_height:
    #         new_height = max_height
    #     self.msg_edit.setFixedHeight(new_height)

    def set_status_text(self, text: str):
        self.__status_label.setText(text)


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow(Model('testuser'))
    main_window.show()
    main_window.set_type_area_visibility(True)
    sys.exit(app.exec())
