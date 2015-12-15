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
             QUEUE_RECV_MESSAGES=False,
             clients_class=connection.Connection,
             auto_register = True):
        """
        :param port: The server port
        :param host: The server host name
        :param BUFFER_SIZE: The maximum size that the server will receive data at one time from a client
        :param QUEUE_SIZE: The maximum number of clients awaiting to be accepted by the server socket
        :param SERVER_EPOLL_BLOCK_TIME:
        :param CLIENT_EPOLL_BLOCK_TIME:
        :param QUEUE_RECV_MESSAGES: Tells wether or not to save the messages received from clients in the
         s.clients[fileno].recv_queue queue.Queue object
        :param connection_objec: The class used for the clients
        :param auto_register: When the server detects new incoming data it unregisters the client in question
        from the epoll object while reading the socket.
        True - Automatically register when server is done receiving from client
        False - When the user is ready to receive new messages from client the user must again register the client to
        the client_epoll object using self.register(fileno)
        """

        self.serve = True # All mainthreads will run aslong as serve is True
        self.host = host
        self.port = port
        self.BUFFER_SIZE = BUFFER_SIZE
        self.SERVER_EPOLL_BLOCK_TIME = SERVER_EPOLL_BLOCK_TIME
        self.CLIENT_EPOLL_BLOCK_TIME = CLIENT_EPOLL_BLOCK_TIME
        self.QUEUE_RECV_MESSAGES = QUEUE_RECV_MESSAGES
        self.clients_class=clients_class
        self.auto_register = auto_register

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
        self.search_readable_thread = threading.Thread(target=self.search_readable)

    def register(self, fileno):
        self.client_epoll.register(fileno, select.EPOLLIN)

    def unregister(self, fileno):
        self.client_epoll.unregister(fileno)

    def accept_clients(self):
        """ Uses the server socket to accept incoming connections
            because the server socket is non-blocking epoll is used to block until a client is ready to be accepted
        """
        while self.serve:
            events = self.server_epoll.poll(self.SERVER_EPOLL_BLOCK_TIME)
            for fileno, event in events:
                if event:
                    try:
                        conn, addr = self.server_socket.accept()
                        self.add_queue.put(self.clients_class(conn, addr, self.QUEUE_RECV_MESSAGES))
                    except BlockingIOError:
                        threading.Thread(target=self.on_warning, args=('Server epoll triggered but got BlockingIOError',)).start()

    def add_client(self):
        """ Adds a client when client is added to the add_queue queue object
        """
        while self.serve:
            conn = self.add_queue.get()
            fileno = conn.fileno()
            self.clients[fileno] = conn
            self.client_epoll.register(fileno, select.EPOLLIN)
            threading.Thread(target=self.on_connect, args=(fileno, )).start()

    def search_readable(self):
        while self.serve:
            events = self.client_epoll.poll(self.CLIENT_EPOLL_BLOCK_TIME)
            for fileno, event in events:
                self.unregister(fileno)
                if event == select.EPOLLIN:
                    self.recv_queue.put(fileno)
                elif event == select.EPOLLERR:
                    threading.Thread(target=self.on_abnormal_disconnect, args=(fileno, 'epoll select.EPOLLERR event')).start()

    def recv_data(self):
        while self.serve:
            fileno = self.recv_queue.get()
            try:
                msg = self.clients[fileno].recv(self.BUFFER_SIZE)
                if self.auto_register:
                    self.register(fileno)
                threading.Thread(target=self.on_recv(fileno, msg))
            except socket.error:
                threading.Thread(target=self.on_abnormal_disconnect, args=(fileno, 'Exception: socket.error while receiving data')).start()
            except connection.Broken:
                threading.Thread(target=self.on_disconnect, args=(fileno,)).start()

    def start(self):
        self.accept_clients_thread.start()
        self.search_readable_thread.start()
        self.recv_data_thread.start()
        self.add_client_thread.start()

        self.on_start()

    # ---------------------------- the "on" functions --------------------------------
    def on_start(self):
        pass

    def on_recv(self, fileno, msg):
        # Triggers when server receives a message from the client
        # The message can be found in conn.recv_buffer where each
        # messages up to self.buffer_size is stored in a list
        pass

    def on_connect(self, fileno):
        pass

    def on_disconnect(self, fileno):
        pass

    def on_abnormal_disconnect(self, fileno, msg):
        pass

    def on_server_shutting_down(self):
        pass

    def on_server_shut_down(self):
        pass

    def on_warning(self, msg):
        pass

    # --------------------------------------------------------------------------------
