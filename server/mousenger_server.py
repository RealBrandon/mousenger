import threading
import time
from socket import *
from model import Model


class Controller:

    def __init__(self):
        self.__model = Model()
        self.__msg_scraper_pool = {}
        self.__is_quitting = False
        self.__thread_pool = []
        self.__thread_pool_lock = threading.Lock()
        self.__scraper_pool_lock = threading.Lock()

    def __login(self, connfd: socket, addr: tuple) -> str | None:
        """Returns None if user disconnects; returns '' if login fails; returns username if login succeeds."""
        connfd.send(b'#OK#')  # Approve the client to proceed.

        username = connfd.recv(16).decode()
        if not username:
            # Empty username, meaning connection breaks
            return None
        elif self.__model.check_if_username_exists(username):
            connfd.send(b'#OK#')  # Username passes.
            password_in_database = self.__model.get_password(username)
            password = connfd.recv(32).decode()  # Receive user input password.
            if not password:
                # Empty password, meaning connection breaks
                return None
            elif password == password_in_database:
                connfd.send(b'#OK#')
                self.__model.toggle_online_status(username, addr)
                print(f'User "{username}" from {addr} is logged in.')
                return username
            else:  # Invalid password
                connfd.send(b'#NO#')
                print(f'Login from {addr} failed.')
                return ''

        else:  # Invalid username
            connfd.send(b'#NO#')
            print(f'Login from {addr} failed.')
            return ''

    def __logout(self, username: str):
        self.__model.toggle_online_status(username)
        print(f'User "{username}" is logged out.')

    def __relay_msg(self, connfd: socket, sender: str):
        connfd.send(b'#OK#')  # Approve the client to proceed.
        data = connfd.recv(256).decode()
        if not data:
            # Client disconnects. Relay method aborted.
            return

        connfd.send(b'#OK#')
        data = data.strip('#')
        data = data.split('#END')[0]
        receiver, message = data.split('#')
        print(f'{sender} => {receiver}: {message}')

        if self.__model.get_is_online(receiver):  # Receiver is online. Send the message.
            message = f'#{sender}#{message}#END#'
            self.__model.add_into_msg_pool(receiver, message)
        else:  # Receiver is offline. Cache the message onto server.
            pass

    def __find_user(self, connfd: socket):
        connfd.send(b'#OK#')
        query = connfd.recv(16).decode()
        if self.__model.check_if_username_exists(query):
            connfd.send(b'#OK#')
        else:
            connfd.send(b'#NO#')

    def __msg_feeder(self, username: str):
        """One client, one feeder thread"""
        while username not in self.__msg_scraper_pool:  # In case the scraper of the user hasn't reached the server
            time.sleep(0.1)
        self.__scraper_pool_lock.acquire()
        connfd = self.__msg_scraper_pool.pop(username)
        self.__scraper_pool_lock.release()

        short_sleep_count = 0
        while not self.__is_quitting and self.__model.get_is_online(username):
            message = self.__model.get_oldest_from_msg_pool(username)
            if not message:
                # Message is empty. Sleep.
                if short_sleep_count < 5:
                    time.sleep(0.1)
                    short_sleep_count += 1
                else:
                    time.sleep(1)
                    short_sleep_count = 0
            else:
                connfd.send(message.encode())
        connfd.close()

    def __msg_scraper_handler(self, handler_sock: socket):
        while not self.__is_quitting:
            connfd, client_addr = handler_sock.accept()
            username = connfd.recv(16).decode()
            self.__scraper_pool_lock.acquire()
            self.__msg_scraper_pool[username] = connfd
            self.__scraper_pool_lock.release()

    def __request_handler(self, connfd: socket, client_addr: tuple):
        """One client, one handler thread, one connfd."""
        try:
            while not self.__is_quitting:
                signal = connfd.recv(8)
                if signal == b'#MSG#':
                    self.__relay_msg(connfd, username)

                elif signal == b'#FIND#':
                    self.__find_user(connfd)

                elif signal == b'#LOGIN#':
                    username = self.__login(connfd, client_addr)
                    if username is None:
                        break  # User disconnects. Handler stops.
                    elif username == '':
                        break  # Login failed. Handler stops.

                    thread = threading.Thread(target=self.__msg_feeder,
                                              args=(username,), daemon=True)
                    thread.start()  # Message feeder starts.
                    self.__thread_pool_lock.acquire()
                    self.__thread_pool.append(thread)
                    self.__thread_pool_lock.release()

                elif signal == b'#LOGOUT#':
                    self.__logout(username)
                    break

                elif signal == b'':
                    print('The client is disconnected.')
                    print(f'Request handler for client {client_addr} aborted')
                    self.__logout(username)
                    break

                else:
                    print(f'Non-handleable signals sent by the client {client_addr}!')

        except OSError as err_msg:
            print(str(err_msg))
        finally:
            connfd.close()

    def main(self):
        handler_spawner_sock = socket(AF_INET, SOCK_STREAM)
        handler_spawner_sock.bind(('0.0.0.0', 12345))
        handler_spawner_sock.listen(10)

        scraper_handler_sock = socket(AF_INET, SOCK_STREAM)
        scraper_handler_sock.bind(('0.0.0.0', 18964))
        scraper_handler_sock.listen(10)

        thread = threading.Thread(target=self.__msg_scraper_handler,
                                  args=(scraper_handler_sock,), daemon=True)
        thread.start()
        self.__thread_pool.append(thread)
        print('Server started.')

        try:
            while True:  # Spawn request handler for every client
                connfd, client_addr = handler_spawner_sock.accept()
                thread = threading.Thread(target=self.__request_handler,
                                          args=(connfd, client_addr),
                                          daemon=True)
                thread.start()
                self.__thread_pool_lock.acquire()
                self.__thread_pool.append(thread)
                self.__thread_pool_lock.release()

                self.__thread_pool_lock.acquire()
                for thread in self.__thread_pool:  # Thread pool clean-up
                    if not thread.is_alive():
                        thread.join()
                        self.__thread_pool.remove(thread)
                self.__thread_pool_lock.release()
                print(f'{len(self.__thread_pool)} child thread(s) running...')

        except KeyboardInterrupt:
            print('\r  ')
            print('**************************************')
            print('Keyboard Interruption by admin')

        finally:
            self.__is_quitting = True
            handler_spawner_sock.close()
            scraper_handler_sock.close()
            # [thread.join() for thread in self.__thread_pool]

        print('Server stopped.')


if __name__ == '__main__':
    server = Controller()
    server.main()
