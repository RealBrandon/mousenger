import os
from PyQt6 import QtCore
# from PyQt6.QtCore import pyqtSignal, QObject

MAX_MSG_QUEUE_LEN = 20


class Model(QtCore.QObject):
    msgStoreUpdated = QtCore.pyqtSignal()
    chatTitleChanged = QtCore.pyqtSignal()
    chatListChanged = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.__username = None
        # Create necessary directories if not present
        os.makedirs(f"./data/{self.__username}/chat_history", exist_ok=True)
        # Initialise chat_list from the files in chat_history.
        self.__chat_list = [filename.rsplit(".", 1)[0] for filename in
                            os.listdir(f"./data/{self.__username}/chat_history")]
        # There is an annoying thing with rstrip().
        # "bot.dat".rstrip(".dat") gives "bo" only.
        # Therefore, rsplit() is used instead.
        self.__msg_buffer = {chat_title: None for chat_title in self.__chat_list}
        self.__load_into_msg_store()
        self.__opened_chat_name = ""
        self.__logged_in = False

    def is_logged_in(self) -> bool:
        """Check if the current user is logged in."""
        return self.__logged_in

    def toggle_logged_in(self):
        self.__logged_in = not self.__logged_in

    def set_username(self, new_username: str):
        self.__username = new_username

    def get_chat_list(self) -> list:
        return self.__chat_list

    def __check_is_in_chat_list(self, chat_title: str) -> bool:
        if chat_title in self.__chat_list:
            return True
        else:
            return False

    def __move_to_top_of_chat_list(self, chat_title: str):
        self.__chat_list.remove(chat_title)
        self.__chat_list.insert(0, chat_title)

        self.chatListChanged.emit()

    def __add_to_chat_list(self, chat_title: str):
        self.__chat_list.append(chat_title)
        if not self.__check_is_in_msg_store(chat_title):  # Add to msg_store if needed.
            self.__add_chat_to_msg_store(chat_title)

        self.chatListChanged.emit()

    def get_opened_chat_name(self) -> str:
        return self.__opened_chat_name

    def set_opened_chat_name(self, new_chat_name: str):
        if not self.__check_is_in_chat_list(new_chat_name):
            self.__add_to_chat_list(new_chat_name)
        self.__opened_chat_name = new_chat_name

        self.chatTitleChanged.emit()

    def save_to_msg_store(self, raw_msg: str, is_self: bool = True, chat_title: str = None):
        """Default to sending by user themselves in the current chat"""
        if chat_title is None:
            chat_title = self.get_opened_chat_name()

        if is_self:  # Check if the message is sent by the user themselves.
            sender = "You"
        else:
            sender = chat_title

        if chat_title not in self.__msg_buffer:  # Check if chat is present.
            self.__add_chat_to_msg_store(chat_title)

        self.__msg_buffer[chat_title].append((sender, raw_msg))
        if chat_title == self.__opened_chat_name:  # Check if notifying controller and view is needed
            self.msgStoreUpdated.emit()

    def __add_chat_to_msg_store(self, chat_title: str):
        self.__msg_buffer[chat_title] = []
        if not self.__check_is_in_chat_list(chat_title):  # Add to chat_list if needed.
            self.__add_to_chat_list(chat_title)
        self.__move_to_top_of_chat_list(chat_title)

    def __check_is_in_msg_store(self, chat_title: str) -> bool:
        if chat_title in self.__msg_buffer:
            return True
        else:
            return False

    def get_chat_history(self, chat_title: str = None) -> list:
        """Default to current chat"""
        if chat_title is None:
            chat_title = self.get_opened_chat_name()

        chat_history = []
        for msg_tuple in self.__msg_buffer[chat_title]:
            chat_history.append(msg_tuple)
        return chat_history

    def __load_into_msg_store(self):
        for chat_title in self.__msg_buffer:
            file = open(f"./data/{self.__username}/chat_history/"
                        f"{chat_title}.dat", "r")
            lines = file.readlines()
            file.close()
            remainder = []  # The remaining lines to be written back
            if len(lines) > MAX_MSG_QUEUE_LEN:
                # Only use last n lines if there are too many,
                # where n = MAX_MSG_QUEUE_LEN.
                remainder = lines[:MAX_MSG_QUEUE_LEN * -1]
                lines = lines[MAX_MSG_QUEUE_LEN * -1:]

            self.__msg_buffer[chat_title] = [tuple(line.rstrip("\n").
                                                   split("#SEP#", 1))
                                             for line in lines]
            file = open(f"./data/{self.__username}/chat_history/"
                        f"{chat_title}.dat", "w")
            file.writelines(remainder)
            file.close()

    def dump_msg_buffer(self):
        if self.is_logged_in():
            for chat_title in self.__msg_buffer:
                msg_queue: list = self.__msg_buffer[chat_title]
                queue_len = len(msg_queue)
                if queue_len > MAX_MSG_QUEUE_LEN:
                    file = open(f"./data/{self.__username}/chat_history/"
                                f"{chat_title}.dat", "a")
                    for i in range(queue_len - MAX_MSG_QUEUE_LEN):
                        sender, message = msg_queue.pop(0)  # Dump the oldest message.
                        file.write(f"{sender}#SEP#{message}\n")
                    file.close()
                    if chat_title == self.get_opened_chat_name():
                        self.msgStoreUpdated.emit()
        else:
            for chat_title in self.__msg_buffer:
                file = open(f"./data/{self.__username}/chat_history/"
                            f"{chat_title}.dat", "a")
                msg_queue: list = self.__msg_buffer[chat_title]
                for sender, message in msg_queue:
                    file.write(f"{sender}#SEP#{message}\n")
                file.close()


if __name__ == "__main__":
    data = Model()
