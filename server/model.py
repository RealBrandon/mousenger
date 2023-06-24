from mysql import connector


class Model:

    def __init__(self):
        self.__online_users = {}
        self.__msg_pool = {}

    @staticmethod
    def check_if_username_exists(username: str) -> bool:
        """Check if the username given by user exists in the database"""

        db_conn = connector.connect(
            host='localhost',
            username='mousenger',
            password='mousengerpwd',
            database='mousengerdb'
        )
        cursor = db_conn.cursor()
        query = f'SELECT username FROM users WHERE username = "{username}";'
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        db_conn.close()

        if result is None:
            return False
        else:
            return True

    @staticmethod
    def get_password(username: str) -> str:
        """Check if the password given by user matches the one in the database"""

        db_conn = connector.connect(
            host='localhost',
            username='mousenger',
            password='mousengerpwd',
            database='mousengerdb'
        )
        cursor = db_conn.cursor()
        query = f'SELECT password FROM users WHERE username = "{username}";'
        cursor.execute(query)
        password = cursor.fetchone()[0]
        cursor.close()
        db_conn.close()
        return password

    def get_is_online(self, username: str) -> bool:
        """Check if a specified user is online or not."""
        if username in self.__online_users:
            return True
        else:
            return False

    def toggle_online_status(self, username: str, addr: tuple = None):
        """When making the user go offline, addr argument is not needed."""
        if username in self.__online_users:  # The specified user is online. Log out.
            self.__online_users.pop(username)
        else:  # The specified user is offline. Log in.
            self.__online_users[username] = addr
            self.__msg_pool[username] = []

    # def get_online_users(self) -> str:
    #     result = ''
    #     for user, addr in self.__online_users.items():
    #         result += f'[{user} ip:{addr[0]} port:{addr[1]}]'
    #         result += '\n'
    #
    #     return result

    def add_into_msg_pool(self, receiver: str, sender_n_msg: str):
        if receiver in self.__msg_pool:
            self.__msg_pool[receiver].append(sender_n_msg)
        else:
            self.__msg_pool[receiver] = [sender_n_msg]

    def get_oldest_from_msg_pool(self, receiver: str) -> str:
        try:
            if len(self.__msg_pool[receiver]) > 0:
                message = self.__msg_pool[receiver].pop(0)
            else:
                message = ''
        except IndexError:
            message = ''

        return message
