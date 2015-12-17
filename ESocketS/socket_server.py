#!/bin/env python3
import socket
import threading
import select
from ESocketS import connection
import errno
from queue import Queue


class Socket:
    def __init__(self, port=1234, host=socket.gethostbyname(socket.gethostname()),
             BUFFER_SIZE=2048,
             QUEUE_SIZE=100,
             SERVER_EPOLL_BLOCK_TIME=10,
             CLIENT_EPOLL_BLOCK_TIME=1,
             clients_class=connection.Connection,
             queue_recv_messages=False,
             auto_register=True,
             run_on_in_subthread=True):
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
        :param run_on_in_subthread: Specifies whether or not to run the "on" functions in subthreads using
        threading.Thread
        """

        self.serve = True # All mainthreads will run aslong as serve is True
        self.started = False
        self.host = host
        self.port = port
        self.BUFFER_SIZE = BUFFER_SIZE
        self.QUEUE_SIZE = QUEUE_SIZE
        self.SERVER_EPOLL_BLOCK_TIME = SERVER_EPOLL_BLOCK_TIME
        self.CLIENT_EPOLL_BLOCK_TIME = CLIENT_EPOLL_BLOCK_TIME
        self.queue_recv_messages = queue_recv_messages
        self.clients_class=clients_class
        self.auto_register = auto_register
        self.run_on_in_subthread = run_on_in_subthread

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
        try:
            self.client_epoll.unregister(fileno)
        except FileNotFoundError:
            self.call_on_function(self.on_warning,
                                  ('Tried to unregister a client but client not currently registered', ))

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
                        self.add_queue.put(self.clients_class(conn, addr, self.queue_recv_messages))
                    except BlockingIOError:
                        self.call_on_function(self.on_warning,
                                              ('Server epoll triggered but got BlockingIOError', ))

    def add_client(self):
        """ Adds a client when client is added to the add_queue queue object
        """
        while self.serve:
            conn = self.add_queue.get()
            fileno = conn.fileno()
            self.clients[fileno] = conn
            self.client_epoll.register(fileno, select.EPOLLIN)
            self.call_on_function(self.on_connect,
                                  (fileno, ))

    def search_readable(self):
        while self.serve:
            events = self.client_epoll.poll(self.CLIENT_EPOLL_BLOCK_TIME)
            for fileno, event in events:
                self.unregister(fileno)
                if event == select.EPOLLIN:
                    self.recv_queue.put(fileno)
                elif event == select.EPOLLERR:
                    self.call_on_function(self.on_abnormal_disconnect,
                                          (fileno, 'epoll select.EPOLLERR event'))

    def recv_data(self):
        while self.serve:
            fileno = self.recv_queue.get()
            try:
                msg = self.clients[fileno].recv(self.BUFFER_SIZE)
                if self.auto_register:
                    self.register(fileno)
                self.call_on_function(self.on_recv,
                                      (fileno, msg))
            except socket.error:
                self.call_on_function(self.on_abnormal_disconnect,
                                      (fileno, 'Exception: socket.error while receiving data'))
            except connection.Broken:
                self.call_on_function(self.on_disconnect,
                                      (fileno, ))

    def start(self):
        if self.started:
            raise error('Server can only be started once')
        
        self.started = True
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(self.QUEUE_SIZE)
        
        self.accept_clients_thread.start()
        self.search_readable_thread.start()
        self.recv_data_thread.start()
        self.add_client_thread.start()

        self.call_on_function(self.on_start, ())

    def stop(self):
        self.serve = False
        for i in self.clients:
            self.unregister(i)
            self.close(i)
        self.server_socket.close()
        self.call_on_function(self.on_stop, ())

    def send(self, fileno, msg):
        try:
            self.clients[fileno].send(msg)
        except connection.Broken:
            self.call_on_function(self.on_abnormal_disconnect,
                                  (fileno, 'Failed to send data to client'))
        
    def close(self, fileno):
        try:
            self.clients[fileno].shutdown(socket.SHUT_RDWR)
        except socket.error:
            pass
        self.clients[fileno].close()

    def call_on_function(self, on_function, args):
        if self.run_on_in_subthread:
            threading.Thread(target=on_function, args=args).start()
        else:
            on_function(*args)
            
    # ---------------------------- the "on" functions --------------------------------
    def on_start(self):
        pass

    def on_stop(self):
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

    def on_warning(self, msg):
        pass

    # --------------------------------------------------------------------------------

class error(Exception):
    pass
