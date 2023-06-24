import time
import threading
from socket import *

SERVER_IP = '127.0.0.1'
# SERVER_IP = '103.152.220.241'
REQUEST_HANDLER_SPAWNER_ADDR = (SERVER_IP, 12345)
MSG_SCRAPER_HANDLER_ADDR = (SERVER_IP, 18964)


class Controller:

    def __init__(self, model, main_window, login_window):
        self.model = model
        self.main_window = main_window
        self.login_window = login_window
        self.connect_login_dialogue_signals()
        self.__sending_sock = None
        self.__thread_pool = []
        # self.__msg_store_lock = threading.Lock()

    def login(self):
        username, password = self.login_window.get_user_input()

        # Abort login if any credential is empty.
        if '' in (username, password):
            self.login_window.set_prompt_text('Credentials cannot be empty!')
            return

        try:
            self.__sending_sock = socket(AF_INET, SOCK_STREAM)
            self.__sending_sock.connect(REQUEST_HANDLER_SPAWNER_ADDR)
            self.__sending_sock.send(b'#LOGIN#')
            result = self.__sending_sock.recv(4)
            if result == b'#OK#':  # Approved by server to proceed.
                del result  # Reset result to avoid errors in further evaluations.
                self.__sending_sock.send(username.encode())
                result = self.__sending_sock.recv(4)  # Receive username check result.
            else:
                result = b'#ERROR#'

        except Exception as error:
            print(str(error), 'while logging in.')
            result = b'#ERROR#'

        if result == b'#OK#':  # Username passes.
            del result
            self.__sending_sock.send(password.encode())
            result = self.__sending_sock.recv(4)  # Receive password check result.

            if result == b'#OK#':  # Password passes. Log in.
                self.login_window.hide()
                self.__main(username)
                return
                # Abort the method to avoid resetting __sending_sock
            elif result == b'#NO#':
                self.login_window.set_prompt_text('Password is incorrect!')

        elif result == b'#NO#':
            self.login_window.set_prompt_text('Username is invalid!')

        if result not in (b'#OK#', b'#NO#'):  # All other cases where error occurs
            self.login_window.set_prompt_text('Sorry, something went wrong. Please try again.')

        # Reset __sending_sock to None to indicate offline status.
        self.__sending_sock.close()
        self.__sending_sock = None

    def send_msg(self):
        user_input = self.main_window.get_msg_edit_input()
        if not user_input:
            # Stops user from sending empty messages.
            self.main_window.set_status_text('Cannot send empty messages!')
            return

        try:
            result = self.__sending_sock.recv(4)
            if result == b'#OK#':
                pass

            self.__sending_sock.send(b'#MSG#')
            message = '#'
            message += self.model.get_opened_chat_name()
            message += '#'
            message += user_input
            message += '#END#'
            self.__sending_sock.send(message.encode())
            result = self.__sending_sock.recv(4)

        except Exception as error:
            print(str(error), 'while sending messages.')
            result = b'#ERROR#'

        if result == b'#OK#':
            self.main_window.clear_msg_edit()
            self.main_window.set_status_text('Sent')
            # self.__msg_store_lock.acquire()
            self.model.save_to_msg_store(user_input)
            # self.__msg_store_lock.release()
        else:
            self.main_window.set_status_text('Failed')

    def msg_scraper(self, username: str):
        """Scrape messages sent to the user from the server feeder"""
        self.__scraper_sock.connect(MSG_SCRAPER_HANDLER_ADDR)
        self.__scraper_sock.send(username.encode())

        while self.model.is_logged_in():
            # If this thread is blocked at recv(),
            # a change in login status won't stop the loop.
            # MORE work needed!!!
            print('Logged in:', self.model.is_logged_in())

            data = self.__scraper_sock.recv(256).decode()
            if not data:
                self.main_window.set_status_text('Disconnected from Server.\n'
                                                   'Please exit and log in again.')
                break  # Empty bytes captured. Server down. Abort scraper.
            data = data.strip('#')
            data = data.split('#END')[0]
            sender, message = data.split('#')
            # self.__msg_store_lock.acquire()
            self.model.save_to_msg_store(message, False, sender)
            # self.__msg_store_lock.release()

        print('msg_scraper aborted.')

    def msg_store_cleaner(self):
        while self.model.is_logged_in():
            # self.__msg_store_lock.acquire()
            self.model.dump_msg_store_data()
            # self.__msg_store_lock.release()
            time.sleep(3.0)

        print('msg_store cleaner aborted.')

    def find_user(self):
        query = self.main_window.get_search_bar_input()
        if not query:
            return  # Search bar is empty. Abort method.

        self.__sending_sock.send(b'#FIND#')
        result = self.__sending_sock.recv(4)
        if result == b'#OK#':
            self.__sending_sock.send(query.encode())
            result = self.__sending_sock.recv(4)
            if result == b'#OK#':  # The enquired user exists.
                self.main_window.set_status_text('1 user is found.')
                self.main_window.set_chat_list([query], )
            elif result == b'#NO#':
                self.main_window.set_status_text('User does not exist.')
            else:
                self.main_window.set_status_text('Sorry, something went wrong.')

    def chat_list_item_activated(self):
        activated_chat_name = self.main_window.get_activated_chat_name()
        self.model.set_opened_chat_name(activated_chat_name)
        # is_online = True  # MORE work needed!!!
        # self.__main_window.set_chat_top(is_online)
        chat_list = self.model.get_chat_list()
        opened_chat_name = self.model.get_opened_chat_name()
        self.main_window.set_chat_list(chat_list, opened_chat_name)  # Restore the chat list to normal after searching.
        self.main_window.set_chat_top(opened_chat_name)
        self.main_window.set_type_area_visibility(True)
        # self.__main_window.adjust_msg_edit_height()

    def connect_login_dialogue_signals(self):
        self.login_window.login_button.clicked.connect(self.login)
        self.login_window.exit_button.clicked.connect(self.exit)

    def connect_other_signals(self):
        self.main_window.send_button.clicked.connect(self.send_msg)
        # self.__main_window.msg_edit.textChanged.connect(self.__main_window.adjust_msg_edit_height)
        self.main_window.msg_edit.returnPressed.connect(self.send_msg)
        self.main_window.exit_action.triggered.connect(self.exit)
        self.main_window.chat_list.itemActivated.connect(self.chat_list_item_activated)
        # The above line enables keyboard selection.
        self.main_window.chat_list.itemClicked.connect(self.chat_list_item_activated)
        # The above line enables mouse click selection.
        self.main_window.search_bar.editingFinished.connect(self.find_user)

        self.model.msgStoreUpdated.connect(self.main_window.update_chat_display)
        self.model.chatTitleChanged.connect(self.main_window.update_chat_display)
        self.model.chatListChanged.connect(self.main_window.set_chat_list)

    def __main(self, username: str):  # Only run after logging in.
        # Instantiate Model after logging in,
        # which contains logged_in = True.
        self.connect_other_signals()
        self.main_window.set_status_text('Logged in!')
        chat_list = self.model.get_chat_list()
        self.main_window.set_chat_list(chat_list,"")
        self.main_window.set_type_area_visibility(False)
        self.main_window.show()

        self.__scraper_sock = socket(AF_INET, SOCK_STREAM)
        thread = threading.Thread(target=self.msg_scraper,
                                  args=(username,), daemon=True)
        thread.start()  # msg_scraper starts.
        self.__thread_pool.append(thread)

        thread = threading.Thread(target=self.msg_store_cleaner, daemon=True)
        thread.start()  # msg_store cleaner starts.
        self.__thread_pool.append(thread)

    def exec(self) -> int:
        self.login_window.show()

        # If __sending_sock is not None, then the user is logged in.
        if self.__sending_sock is not None:
            self.__sending_sock.send(b'#LOGOUT#')
            self.__sending_sock.close()
            print('Logout signal sent.')
            print('Sending socket closed.')

            self.model.toggle_logged_in()  # Toggle login status to terminate child threads.
            [thread.join(2.0) for thread in self.__thread_pool]

            self.__scraper_sock.close()
            print('Scraper socket closed.')
            self.model.dump_msg_store_data()  # Dump all messages in msg_store into files.
            print('All messages dumped.')

