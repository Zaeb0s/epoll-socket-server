#!/bin/env python3
import socket
import threading
import selectors
import queue

class _ClientInfo:
    is_sending = False
    is_registered = False
    data_in_recv_buffer = False
    _send_queue = queue.Queue()
    recv_function = None
    def __init__(self, address):
        self.address = address

def serve_foever(f):
    def wrapper(*args):
        self = args[0]
        try:
            while self.__serve:
                f(*args)
        finally:
            if self.__serve:
                # An error made the server shut down
                self.__serve = False
            elif self._no_serve_alive() == 1:
                # This is the last thread to be closed
                self.on_stop()
                self.__shutdown_wait.set()





class Socket:
    default_recv_buffsize = 4096
    started = False

    __server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    __server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    __server_socket.setblocking(False)

    _sel = selectors.EpollSelector()

    __serve = False
    __shutdown_wait = threading.Event()

    _client_info = {}  # {conn:info_class}
    _accept_queue = queue.Queue()

    def __init__(self,
                 port=1234,
                 host=socket.gethostbyname(socket.gethostname()),
                 queue_size=1000,
                 epoll_block_time=2):

        self.host = host
        self.port = port
        self.queue_size = queue_size
        self.epoll_block_time = epoll_block_time

        self._run_in_subthread = {self.on_recv.__name__: False,
                                  self.on_connect.__name__: False,
                                  self.on_disconnect.__name__: False,
                                  self.on_abnormal_disconnect.__name__: False,
                                  self.on_start.__name__: False,
                                  self.on_stop.__name__: False,
                                  self.on_warning.__name__: False}

        self._serve_threads = {'_recv' :
                                   threading.Thread(target=self._recv),
                               '_accept' :
                                   threading.Thread(target=self._accept),
                               '_handle_connects' :
                                   threading.Thread(target=self._handle_connects)}

    def _recv(self):
        try:
            while self.__serve:
                events = self._sel.select(self.epoll_block_time)
                for key, mask in events:
                    self.unregister(key.fileobj)
                    self._client_info[key.fileobj].data_in_recv_buffer = True
                    self._client_info[key.fileobj].recv_function(key.fileobj)
        finally:
            if self._no_serve_alive() == 1:
                self.__shutdown_wait.set()

    def _accept(self):
        server_epoll = selectors.EpollSelector()
        server_epoll.register(self.__server_socket, selectors.EVENT_READ)
        try:
            while self.__serve:
                server_epoll.select(self.epoll_block_time)
                try:
                    conn, address = self.__server_socket.accept()
                    self._accept_queue.put((conn, address))

                except BlockingIOError:
                    pass
        finally:
            if self._no_serve_alive() == 1:
                self.__shutdown_wait.set()

    def _handle_connects(self):
        while self.__serve:
            try:
                client = self._accept_queue.get(timeout=self.epoll_block_time)
            except queue.Empty:
                pass
            else:
                client[0].setblocking(False)
                self._client_info[client[0]] = _ClientInfo(client[1])
                self._client_info[client[0]].recv_function = self.default_recv_function
                self._call_on_function(self.on_connect, (client[0], ))
                self.register(client[0])
        else:
            if self._no_serve_alive() == 1:
                self.__shutdown_wait.set()

    def register(self, conn):
        try:
            self._sel.register(conn, selectors.EVENT_READ)
        except KeyError:
            # Client is already registered
            self._call_on_function(self.on_warning,
                                   ('Tried to register a client that is already registered:'
                                    ' {}'.format(self._client_info[conn].address),))
        finally:
            self._client_info[conn].is_registered = True
            self._client_info[conn].data_in_recv_buffer = False

    def unregister(self, conn):
        try:
            self._sel.unregister(conn)
        except KeyError:
            # Conn is already not registered
            self._call_on_function(self.on_warning,
                                   ('Tried to unregister a client that is already unregistered:'
                                   ' {}'.format(self._client_info[conn].address),))
        finally:
            self._client_info[conn].is_registered = False

    def start(self):
        if self.started:
            raise OSError('Server can only be started once')
        self.__serve = True
        self.started = True
        self.__server_socket.bind((self.host, self.port))
        self.__server_socket.listen(self.queue_size)

        for thread in self._serve_threads.values():
            thread.start()

        self._call_on_function(self.on_start, ())

    def _no_serve_alive(self):
        """
        Determines how many of the main serve threads are alive
        """
        no_alive = 0
        for thread in self._serve_threads.values():
            if thread.isAlive():
                no_alive += 1
        return no_alive

    def stop(self):

        if not self.started:
            raise OSError("Can't stop server because it has not been started yet")
        self.__serve = False

        # Waiting for the serve forever threads to stop
        self.__shutdown_wait.wait()

        # Disconnecting all users within the selector
        while len(self._sel._fd_to_key) != 0:
            self.disconnect(list(self._sel._fd_to_key.values())[0].fileobj)

        self.__server_socket.shutdown(0)
        self.__server_socket.close()
        self._call_on_function(self.on_stop, ())

    def running(self, option=None):
        if option is None:
            return self.__serve
        elif not option:
            self.__serve = False
            return False
        else:
            raise ValueError('Not a recognized parameter')


    def disconnect(self, conn, normal=True, msg=''):
        if self.client_info(conn).is_registered:
            self.unregister(conn)
        try:
            conn.shutdown(socket.SHUT_RDWR)
        except socket.error:
            pass
        conn.close()
        if normal:
            self._call_on_function(self.on_disconnect, (conn, ))
        else:
            self._call_on_function(self.on_abnormal_disconnect, (conn, msg))
        del self._client_info[conn]

    def send(self, conn, data):
        """
        The send function is coded so that the user can call the send function
        from several different threads at the same time but in order for data not
        to be scrambled only one thread at a time per user is actually sending
        the data the rest is putting the data into a Queue object for the send
        thread.
        Unregisters the user and calls on_abnormal_disconnect if connection broken
        """
        CI = self._client_info[conn]
        if CI.is_sending:
            CI._send_queue.put(data)
        else:
            CI.is_sending = True
            while not CI._send_queue.empty():
                data_to_send = CI._send_queue.get(timeout=0)
                self.send_basic(conn, data_to_send)
            else:
                CI.is_sending = False

    @staticmethod
    def recv_basic(conn, size):
        data = conn.recv(size)
        if data == b'':
            raise BrokenConnection('Received empty bytes array')
        return data

    @staticmethod
    def send_basic(conn, data):
        to_send, total_sent = len(data), 0
        while total_sent < to_send:
            sent = conn.send(data[total_sent:])
            if sent == 0:
                raise BrokenConnection('Sent empty array')


    def default_recv_function(self, conn):
        try:
            data = self.recv_basic(conn, self.default_recv_buffsize)
        except socket.error:
            self.disconnect(conn, False,
                            'Error while receiving data from {}'.format(self.get_ip(conn)))
        except BrokenConnection:
            self.disconnect(conn)
        else:
            self.register(conn)
            self._call_on_function(self.on_recv, (conn, data))
    
    def client_info(self, conn):
        return self._client_info[conn]

    def get_ip(self, conn):
        return self._client_info[conn].address

    def get_clients(self):
        """
        Returns a generator object containing all clients
        """
        return (i for i in self._client_info)

    def run_in_subthread(self, on_function, yes_no):
        """
        Gives the ability to change the _run_in_subthread private variable in an easy way
        if on_functions = 'all' all on_functions are modified
        """
        if yes_no:
            change = True
        else:
            change = False
        if hasattr(on_function, '__name__'):
            name = on_function.__name__
            if name in self._run_in_subthread:
                self._run_in_subthread[on_function.__name__] = change
                return
        elif on_function == 'all':
            for i in self._run_in_subthread:
                self._run_in_subthread[i] = change
            return

        raise ValueError('on_function needs to be one of the ESocketS.Socket() "on" functions')

    def _call_on_function(self, on_function, args):
        if self._run_in_subthread[on_function.__name__]:
            threading.Thread(target=on_function, args=args).start()
        else:
            on_function(*args)

    # ---------------------------- the "on" functions --------------------------------
    def on_start(self):
        pass

    def on_stop(self):
        pass

    def on_recv(self, conn, data):
        pass

    def on_connect(self, conn):
        pass

    def on_disconnect(self, conn):
        pass

    def on_abnormal_disconnect(self, conn, msg):
        pass

    def on_warning(self, msg):
        pass

    # --------------------------------------------------------------------------------


class BrokenConnection(Exception):
    pass
