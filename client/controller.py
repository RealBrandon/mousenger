# Make PyCharm aware of the attributes of other components.
# Allow the use of type hints for other components.
import socket
from model import Model
from ui.main_window import MainWindow
from ui.login_window import LoginWindow

import time
import threading
from socket import *

SERVER_IP = "127.0.0.1"
REQUEST_HANDLER_SPAWNER_ADDR = (SERVER_IP, 12345)
MSG_SCRAPER_HANDLER_ADDR = (SERVER_IP, 18964)


class Controller:

    def __init__(self, model, main_window, login_window):
        self.model: Model = model
        self.main_window: MainWindow = main_window
        self.login_window: LoginWindow = login_window

        self.master_sock = None
        self.scraper_sock = None
        self.thread_pool = []
        # self.__msg_store_lock = threading.Lock()

        self.connect_signals_and_slots()
        self.login_window.show()

    def login(self) -> None | str:
        username, password = self.login_window.get_user_input()
        # Abort login if any credential is empty.
        if "" in (username, password):
            self.login_window.set_prompt_text("Credentials cannot be empty!")
            return

        try:
            self.master_sock = socket(AF_INET, SOCK_STREAM)
            self.master_sock.connect(REQUEST_HANDLER_SPAWNER_ADDR)
            self.master_sock.send(b"#LOGIN#")
            result = self.master_sock.recv(4)

            if result == b"#OK#":  # Approved by server to proceed.
                del result  # Reset result to avoid errors in further evaluations.
                self.master_sock.send(username.encode())
                result = self.master_sock.recv(4)  # Receive username check result.
        except Exception as err:
            result = b"#ERROR#"
            if __debug__:
                print("login:", str(err), "while checking username with server.")

        if result == b"#OK#":  # Username passes.
            del result
            try:
                self.master_sock.send(password.encode())
                result = self.master_sock.recv(4)  # Receive password check result.
            except Exception as err:
                result = b"#ERROR#"
                if __debug__:
                    print("login:", str(err), "while checking password with server.")

            if result == b"#OK#":  # Password passes. Log in.
                return username  # Abort the method to preserve master_sock.
            elif result == b"#NO#":
                self.login_window.set_prompt_text("Password is incorrect!")
        elif result == b"#NO#":  # Username does not pass.
            self.login_window.set_prompt_text("Username is invalid!")

        if result not in (b"#OK#", b"#NO#"):  # All other cases
            self.login_window.set_prompt_text("Sorry, something went wrong. Please try again.")
        # Reset master_sock for next login attempt.
        self.master_sock.close()
        self.master_sock = None

    def send_msg(self):
        user_input = self.main_window.get_msg_edit_input()
        if not user_input:
            # Stop user from sending empty messages.
            self.main_window.set_status_text("Cannot send empty messages!")
            return

        try:
            self.master_sock.send(b"#MSG#")
            result = self.master_sock.recv(4)
            if result == b"#OK#":  # Approved by server to proceed.
                del result  # Reset result to avoid errors in further evaluations.
                message = "#"
                message += self.model.get_opened_chat_name()
                message += "#"
                message += user_input
                message += "#END#"
                self.master_sock.send(message.encode())
                result = self.master_sock.recv(4)  # Receive message transmission result.
        except Exception as err:
            if __debug__:
                print("send_msg:", str(err), "while sending messages.")
            result = b"#ERROR#"

        if result == b"#OK#":
            self.main_window.clear_msg_edit()
            self.main_window.set_status_text("Sent")
            # self.__msg_store_lock.acquire()
            self.model.save_to_msg_store(user_input)
            # self.__msg_store_lock.release()
        elif result == b"#ERROR#":
            self.main_window.set_status_text("Failed to send. Please try again.")
        else:
            self.main_window.set_status_text("Unexpected error occurred. Please try again.")

    def msg_scraper(self, username: str):
        """Scrape messages sent to the user from the server feeder"""
        self.scraper_sock.connect(MSG_SCRAPER_HANDLER_ADDR)
        self.scraper_sock.send(username.encode())

        if __debug__:
            counter = 0
        while self.model.is_logged_in():
            # If this thread is blocked at recv(),
            # a change in login status won't stop the loop.
            # MORE work needed!!!

            data = self.scraper_sock.recv(256).decode()
            if not data:  # Empty bytes captured. Server down. Abort scraper.
                self.main_window.set_status_text("Disconnected from Server.\n"
                                                 "Please exit and log in again.")
                break
            data = data.strip("#")
            data = data.split("#END")[0]
            sender, message = data.split("#")
            # self.__msg_store_lock.acquire()
            self.model.save_to_msg_store(message, False, sender)
            # self.__msg_store_lock.release()
            if __debug__:
                counter += 1
                print("msg_scraper:", counter, "loop(s) finished")

        if __debug__:
            print("msg_scraper: Aborted")

    def msg_buffer_cleaner(self):
        if __debug__:
            counter = 0
        while self.model.is_logged_in():
            # self.__msg_store_lock.acquire()
            self.model.dump_msg_buffer()
            # self.__msg_store_lock.release()
            time.sleep(3.0)
            if __debug__:
                counter += 1
                print("msg_buffer_cleaner:", counter, "loop(s) finished")

        if __debug__:
            print("msg_buffer_cleaner: Aborted")

    def find_user(self):
        query = self.main_window.get_search_bar_input()
        if not query:
            return  # Search bar is empty. Abort method.

        self.master_sock.send(b"#FIND#")
        result = self.master_sock.recv(4)
        if result == b"#OK#":
            self.master_sock.send(query.encode())
            result = self.master_sock.recv(4)
            if result == b"#OK#":  # The enquired user exists.
                self.main_window.set_status_text("1 user is found.")
                self.model.set_opened_chat_name(query)
                self.set_chat_list()
            elif result == b"#NO#":
                self.main_window.set_status_text("User does not exist.")
            else:
                self.main_window.set_status_text("Sorry, something went wrong.")

    def set_chat_top(self):
        """Wrapper method of ui.main_window.MainWindow.set_chat_top"""
        opened_chat_name = self.model.get_opened_chat_name()
        self.main_window.set_chat_top_bar(opened_chat_name)

    def set_chat_list(self):
        """Wrapper method of ui.main_window.MainWindow.set_chat_list"""
        chat_list = self.model.get_chat_list()
        opened_chat_name = self.model.get_opened_chat_name()
        self.main_window.set_chat_list(chat_list, opened_chat_name)

    def update_chat_display(self):
        """Wrapper method of ui.main_window.MainWindow.update_chat_display"""
        chat_history: list = self.model.get_chat_history()
        self.main_window.set_chat_display(chat_history)

    def chat_list_item_activated(self):
        activated_chat_name = self.main_window.get_activated_chat_name()
        self.model.set_opened_chat_name(activated_chat_name)
        # is_online = True  # MORE work needed!!!
        # self.__main_window.set_chat_top(is_online)
        self.set_chat_list()  # Restore the chat list to normal after searching.
        self.set_chat_top()
        self.main_window.set_type_area_visibility(True)
        # self.__main_window.adjust_msg_edit_height()

    def connect_signals_and_slots(self):
        self.login_window.login_button.clicked.connect(self.main)

        self.main_window.send_button.clicked.connect(self.send_msg)
        # self.__main_window.msg_edit.textChanged.connect(self.__main_window.adjust_msg_edit_height)
        self.main_window.msg_edit.returnPressed.connect(self.send_msg)
        self.main_window.chat_list.itemActivated.connect(
            self.chat_list_item_activated)  # Enables keyboard selection in chat list.
        self.main_window.chat_list.itemClicked.connect(
            self.chat_list_item_activated)  # Enables mouse click selection in chat list.
        self.main_window.search_bar.editingFinished.connect(self.find_user)
        self.main_window.aboutToClose.connect(self.exit)

        self.model.msgStoreUpdated.connect(self.update_chat_display)
        self.model.chatTitleChanged.connect(self.update_chat_display)
        self.model.chatListChanged.connect(self.set_chat_list)

    def main(self):
        username = self.login()
        if username is None:
            return  # Login fails. Abort main thread.
        self.model.toggle_logged_in()
        self.login_window.hide()
        if __debug__:
            print("main: logged_in =", self.model.is_logged_in())
        self.model.set_username(username)

        self.main_window.set_status_text("Logged in!")
        self.set_chat_list()
        self.main_window.set_type_area_visibility(False)
        self.main_window.show()  # Make sure this line is below other lines of setting the main window.

        self.scraper_sock = socket(AF_INET, SOCK_STREAM)
        thread = threading.Thread(target=self.msg_scraper,
                                  name="message scraper",
                                  args=(username,),
                                  daemon=True)
        thread.start()  # msg_scraper starts.
        self.thread_pool.append(thread)

        thread = threading.Thread(target=self.msg_buffer_cleaner,
                                  name="message buffer cleaner",
                                  daemon=True)
        thread.start()  # msg_buffer_cleaner starts.
        self.thread_pool.append(thread)

    def exit(self):
        self.main_window.set_status_text("Wrapping up... Please wait a moment.")
        if self.model.is_logged_in():
            self.master_sock.send(b"#LOGOUT#")
            if __debug__:
                print("exit: Logout signal sent")
            self.master_sock.close()
            if __debug__:
                print("exit: Master socket closed")

            self.model.toggle_logged_in()  # Toggle login status to terminate child threads.
            thread: threading.Thread
            for thread in self.thread_pool:
                thread.join(2.0)
                if __debug__:
                    if thread.is_alive():
                        print(f"exit: {thread} failed to terminate before timeout.")
                    else:
                        print(f"exit: {thread} terminated")

            self.scraper_sock.close()
            if __debug__:
                print("exit: Scraper socket closed")
            self.model.dump_msg_buffer()  # Dump all buffered messages into files.
            if __debug__:
                print("exit: Message buffer dumped")
