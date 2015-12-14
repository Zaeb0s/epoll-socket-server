#!/bin/env python3
import socket
import threading
import select
from ESocketS import connection
import errno
from queue import Queue


class Socket(object):
    def __init__(self, port=1234, host=socket.gethostbyname(socket.gethostname()),
             BUFFER_SIZE=2048,
             QUEUE_SIZE=100,
             SERVER_EPOLL_BLOCK_TIME=10,
             CLIENT_EPOLL_BLOCK_TIME=1,
             QUEUE_RECV_MESSAGES=False):
        """
        :param port: The server port
        :param host: The server host name
        :param BUFFER_SIZE: The maximum size that the server will receive data at one time from a client
        :param QUEUE_SIZE: The maximum number of clients awaiting to be accepted by the server socket
        :param SERVER_EPOLL_BLOCK_TIME:
        :param CLIENT_EPOLL_BLOCK_TIME:
        :param QUEUE_RECV_MESSAGES: Tells wether or not to save the messages received from clients in the
         s.clients[fileno].recv_queue queue.Queue object
        """
        # If no host is given the server is hosted on the local ip

        self.serve = True # All mainthreads will run aslong as serve is True
        self.host = host
        self.port = port
        self.BUFFER_SIZE = BUFFER_SIZE
        self.SERVER_EPOLL_BLOCK_TIME = SERVER_EPOLL_BLOCK_TIME
        self.CLIENT_EPOLL_BLOCK_TIME = CLIENT_EPOLL_BLOCK_TIME
        self.QUEUE_RECV_MESSAGES = QUEUE_RECV_MESSAGES

        # Starting the server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen(QUEUE_SIZE)
        self.server_socket.setblocking(0)

        self.server_epoll = select.epoll()
        self.server_epoll.register(self.server_socket.fileno(), select.EPOLLIN)
        self.client_epoll = select.epoll()

        self.clients = {}  # {fileno:clientobj}

        self.add_queue = Queue(0)
        self.recv_queue = Queue(0)

        # The four main threads
        self.accept_clients_thread = threading.Thread(target=self.accept_clients)  # Uses the server socket to accept new clients
        self.recv_data_thread = threading.Thread(target=self.recv_data)  # Uses the client sockets to recv data
        self.add_client_thread = threading.Thread(target=self.add_client) # Uses the add_queue to register new clients

    def accept_clients(self):
        """ Uses the server socket to accept incoming connections
            because the server socket is non-blocking epoll is used to block until a client is ready to be accepted
        """
        while self.serve:
            events = self.server_epoll.poll(self.SERVER_EPOLL_BLOCK_TIME)
            for fileno, event in events:
                if event:
                    conn, addr = self.server_socket.accept()
                    self.add_queue.put(connection.Connection(conn, addr, self.QUEUE_RECV_MESSAGES))

    def add_client(self):
        """ Adds a client when client is added to the add_queue queue object
        """
        while self.serve:
            conn = self.add_queue.get()
            fileno = conn.fileno()
            self.clients[fileno] = conn
            self.client_epoll.register(fileno, select.EPOLLIN)
            threading.Thread(target=self.on_client_connect, args=(fileno, )).start()

    def recv_data(self):
        """ Receives data from clients and adds it to the recv queue
        """
        while self.serve:
            events = self.client_epoll.poll(self.CLIENT_EPOLL_BLOCK_TIME)
            for fileno, event in events:
                if event:
                    try:
                        data = self.clients[fileno].recv(self.BUFFER_SIZE)
                    except socket.error as e:
                        if e.args[0] not in (errno.EWOULDBLOCK, errno.EAGAIN):
                            # since this is a non-blocking socket.
                            self.unregister(fileno)
                        continue
                    except connection.Broken:
                        self.unregister(fileno)
                        continue

                    threading.Thread(target=self.on_message_recv, args=(fileno, data)).start()

    def unregister(self, fileno):
        try:
            self.client_epoll.unregister(fileno)
            threading.Thread(target=self.on_client_disconnect, args=(fileno,)).start()
        except FileNotFoundError:
            self.on_warning('Failed to remove: %s because client not registered in the epoll object' % conn.getip())

    def start(self):
        self.accept_clients_thread.start()
        self.recv_data_thread.start()
        self.add_client_thread.start()
        self.on_start()

    # ---------------------------- the "on" functions --------------------------------
    def on_client_connect(self, fileno):
        pass

    def on_start(self):
        pass

    def on_message_recv(self, fileno, data):
        # Triggers when server receives a message from the client
        # The message can be found in conn.recv_buffer where each
        # messages up to self.buffer_size is stored in a list
        pass

    def on_client_disconnect(self, fileno):
        pass

    def on_server_shutting_down(self):
        pass

    def on_server_shut_down(self):
        pass

    def on_warning(self, msg):
        pass

    # --------------------------------------------------------------------------------


if __name__ == '__main__':
    class sock(Socket):

        def on_start(self):
            print('Server started on: ', self.host, self.port)

        def on_client_connect(self, fileno):
            print(self.clients[fileno].getip(), 'Connected')
            pass

        def on_message_recv(self, fileno, msg):
            print(msg)

        def on_client_disconnect(self, fileno):
            print(self.clients[fileno].getip(), 'Disconnected')

            pass

        def on_server_shutting_down(self):
            print('Server shutting down')

        def on_server_shut_down(self):
            print('Server is now closed')

        def on_warning(self, msg):
            print('Warning: ', msg)

    s = sock(QUEUE_RECV_MESSAGES='localhost')
    s.start()
