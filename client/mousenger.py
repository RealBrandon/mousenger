import sys
import time
import threading
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from socket import *
from model import Model
from ui.main_window import MainWindow
from ui.login_dialogue import LoginDialogue

IS_DEBUGGING = True
# SERVER_IP = '127.0.0.1'
SERVER_IP = '103.152.220.241'
REQUEST_HANDLER_SPAWNER_ADDR = (SERVER_IP, 12345)
MSG_SCRAPER_HANDLER_ADDR = (SERVER_IP, 18964)


class Controller(QApplication):

    def __init__(self):
        super().__init__(sys.argv)
        self.setWindowIcon(QIcon('./ui/happy_mouse.webp'))
        self.__login_dialogue = LoginDialogue()
        self.__connect_login_dialogue_signals()
        self.__sending_sock = socket(AF_INET, SOCK_STREAM)
        self.__thread_pool = []
        # self.__msg_store_lock = threading.Lock()

    def __login(self):
        try:
            self.__sending_sock.connect(REQUEST_HANDLER_SPAWNER_ADDR)
            self.__sending_sock.send(b'#LOGIN#')
            time.sleep(0.2)  # To avoid TCP sticky packets

            username, password = self.__login_dialogue.get_user_input()
            if '' in (username, password):
                self.__login_dialogue.set_prompt_text('Neither username or password can be empty!')
                result = b'#EMPTY#'
            else:
                self.__sending_sock.send(username.encode())  # Check username
                result = self.__sending_sock.recv(4)

        except ConnectionError as err:
            if IS_DEBUGGING:
                print(str(err), 'while logging in.')
            result = b'#ERROR#'

        if result == b'#OK#':  # Username is valid.
            result = None  # Reset result to avoid confusions in the following if statements.
            self.__sending_sock.send(password.encode())  # Check password
            result = self.__sending_sock.recv(4)

            if result == b'#OK#':  # Password is correct. Logged in.
                self.__login_dialogue.hide()
                self.__main(username)
                return  # Avoid running the code for socket recreation.

            elif result == b'#NO#':  # Password is wrong
                self.__login_dialogue.set_prompt_text('Password is incorrect!')

        elif result == b'#NO#':  # Username is invalid.
            self.__login_dialogue.set_prompt_text('Username is invalid!')

        if result not in (b'#OK#', b'#NO#', b'#EMPTY#'):  # All other cases
            self.__login_dialogue.set_prompt_text('Sorry, something went wrong. Please try again.')

        # Recreate the sending socket to avoid repeated connection to the server.
        self.__sending_sock.close()
        self.__sending_sock = socket(AF_INET, SOCK_STREAM)

    def __send_msg(self):
        try:
            self.__sending_sock.send(b'#MSG#')
            user_input = self.__main_window.get_msg_edit_input()
            message = '#'
            message += self.__model.get_cur_chat_title()
            message += '#'
            message += user_input
            message += '#END#'
            self.__sending_sock.send(message.encode())
            result = self.__sending_sock.recv(4)
        except BrokenPipeError as err:
            if IS_DEBUGGING:
                print(str(err), 'while sending messages.')
            result = b'#ERROR#'

        if result == b'#OK#':
            self.__main_window.clear_msg_edit()
            self.__main_window.set_status_text('Sent')
            # self.__msg_store_lock.acquire()
            self.__model.save_to_msg_store(user_input)
            # self.__msg_store_lock.release()
        else:
            self.__main_window.set_status_text('Failed')

    def __msg_scraper(self, username: str):
        '''Scrape messages sent to the user from the server feeder'''
        self.__scraper_sock.connect(MSG_SCRAPER_HANDLER_ADDR)
        self.__scraper_sock.send(username.encode())

        while self.__model.is_logged_in():
            # If this thread is blocked at recv(),
            # a change in login status won't stop the loop.
            # MORE work needed!!!
            if IS_DEBUGGING:
                print('Logged in:',self.__model.is_logged_in())

            data = self.__scraper_sock.recv(256).decode()
            if not data:
                self.__main_window.set_status_text('Disconnected from Server.\n'
                                                   'Please exit and log in again.')
                break  # Empty bytes captured. Server down. Abort scraper.
            data = data.strip('#')
            data = data.split('#END')[0]
            sender, message = data.split('#')
            # self.__msg_store_lock.acquire()
            self.__model.save_to_msg_store(message, False, sender)
            # self.__msg_store_lock.release()

        if IS_DEBUGGING:
            print('msg_scraper aborted.')

    def __msg_store_cleaner(self):
        while self.__model.is_logged_in():
            # self.__msg_store_lock.acquire()
            self.__model.dump_msg_store_data()
            # self.__msg_store_lock.release()
            time.sleep(3.0)

        if IS_DEBUGGING:
            print('msg_store cleaner aborted.')

    def __find_user(self):
        query = self.__main_window.get_search_bar_input()
        if not query:
            return  # Search bar is empty. Abort method.

        self.__sending_sock.send(b'#FIND#')
        result = self.__sending_sock.recv(4)
        if result == b'#OK#':
            self.__sending_sock.send(query.encode())
            result = self.__sending_sock.recv(4)
            if result == b'#OK#':  # The enquired user exists.
                self.__main_window.set_status_text('1 user is found.')
                self.__main_window.set_chat_list([query])
            elif result == b'#NO#':
                self.__main_window.set_status_text('User does not exist.')
            else:
                self.__main_window.set_status_text('Sorry, something went wrong.')

    def __chat_list_item_activated(self):
        chat_title = self.__main_window.get_activated_chat_title()
        self.__model.set_cur_chat_title(chat_title)
        # is_online = True  # MORE work needed!!!
        # self.__main_window.set_chat_top(is_online)
        self.__main_window.set_chat_list()  # Restore the chat list to normal after searching.
        self.__main_window.set_chat_top()
        self.__main_window.set_type_area_visibility(True)
        self.__main_window.adjust_msg_edit_height()

    def __connect_login_dialogue_signals(self):
        self.__login_dialogue.login_button.clicked.connect(self.__login)
        self.__login_dialogue.exit_button.clicked.connect(self.exit)

    def __connect_other_signals(self):
        self.__main_window.send_button.clicked.connect(self.__send_msg)
        self.__main_window.msg_edit.textChanged.connect(self.__main_window.adjust_msg_edit_height)
        self.__main_window.exit_action.triggered.connect(self.exit)
        self.__main_window.chat_list.itemActivated.connect(self.__chat_list_item_activated)  # Enable keyboard selection
        self.__main_window.chat_list.itemClicked.connect(
            self.__chat_list_item_activated)  # Enable mouse click selection
        self.__main_window.search_bar.editingFinished.connect(self.__find_user)

        self.__model.msgStoreUpdated.connect(self.__main_window.update_chat_display)
        self.__model.chatTitleChanged.connect(self.__main_window.update_chat_display)
        self.__model.chatListChanged.connect(self.__main_window.set_chat_list)

    def __main(self, username: str):  # Only run after logging in.
        # Instantiate Model after logging in,
        # which contains logged_in = True.
        self.__model = Model(username)
        self.__main_window = MainWindow(self.__model)
        self.__connect_other_signals()
        self.__main_window.set_status_text('Logged in!')
        self.__main_window.set_chat_list()
        self.__main_window.set_type_area_visibility(False)
        self.__main_window.show()

        self.__scraper_sock = socket(AF_INET, SOCK_STREAM)
        thread = threading.Thread(target=self.__msg_scraper,
                                  args=(username,), daemon=True)
        thread.start()  # msg_scraper starts.
        self.__thread_pool.append(thread)

        thread = threading.Thread(target=self.__msg_store_cleaner, daemon=True)
        thread.start()  # msg_store cleaner starts.
        self.__thread_pool.append(thread)

    def exec(self) -> int:
        self.__login_dialogue.show()
        exit_code = super().exec()

        # If __model is present, then the user is logged in.
        if '_Controller__model' in self.__dir__():
            self.__sending_sock.send(b'#LOGOUT#')
            if IS_DEBUGGING:
                print('Logout signal sent.')
            self.__model.toggle_logged_in()  # Toggle login status to terminate child threads.
            [thread.join(2.0) for thread in self.__thread_pool]
            self.__scraper_sock.close()
            if IS_DEBUGGING:
                print('Scraper socket closed.')
            self.__model.dump_msg_store_data()  # Dump all messages in msg_store into files.
            if IS_DEBUGGING:
                print('All messages dumped.')

        self.__sending_sock.close()
        return exit_code


if __name__ == '__main__':
    client = Controller()
    sys.exit(client.exec())
