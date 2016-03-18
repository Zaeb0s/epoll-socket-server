#!/bin/env python3
import selectors
import socket
import loopfunction
import logging
import maxthreads
from threading import Lock
from errno import EALREADY, EINPROGRESS, EWOULDBLOCK, ECONNRESET, EINVAL, \
     ENOTCONN, ESHUTDOWN, EISCONN, EBADF, ECONNABORTED, EPIPE, EAGAIN, \
     errorcode

_DISCONNECTED = frozenset({ECONNRESET, ENOTCONN, ESHUTDOWN, ECONNABORTED, EPIPE,
                           EBADF})

class ConnectionClosed(Exception):
    pass

clients = []
clients_selector = selectors.EpollSelector()
server_selector = selectors.EpollSelector()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.setblocking(False)

server_selector.register(server_socket, selectors.EVENT_READ)

class ClientHandler:
    def __init__(self):

        self.socket = None
        self.address = None
        self._send_lock = Lock()
        self.socket_closed = False
        self.socket_registered = False

        clients.append(self)

    def _handle_socket_accept(self):
        try:
            value = self.handle_socket_accept()
            if value is True:
                self.selector_register()
            else:
                self.close(value or '')
        except ConnectionClosed as why: 
            # Catching expected errors
            self.close(str(why))

    def _handle_socket_message(self):
        try:
            value = self.handle_socket_message()
            if value is True:
                self.selector_register()
            else:
                self.close(value or '')
        except ConnectionClosed as why: 
            # Catching expected errors
            self.close(str(why))

    def handle_socket_accept(self):
        """Return string or False: the socket is closed and handle_socket_close is called with
         reason=string/''. Return True the socket is registered to the client selector
        """
        return True

    def handle_socket_message(self):
        """Return string or False: the socket is closed and handle_socket_close is called
         with reason=string/'' Return True the socket is registered to the client selector
        """
        pass

    def handle_socket_close(self, reason):
        """Called before the socket is closed
        """
        pass

    def fileno(self):
        return self.socket.fileno()

    def selector_register(self):
        self.socket_registered = True
        clients_selector.register(self, selectors.EVENT_READ)

    def selector_unregister(self):
        self.socket_registered = False
        clients_selector.unregister(self)

    def close(self, reason, how=socket.SHUT_RDWR):
        try:
            self.socket_closed = True
            self.handle_socket_close(reason)
            if self.socket_registered:
                self.selector_unregister()
            clients.remove(self)
            try:
                self.socket.shutdown(how)
            except socket.error:
                pass
            self.socket.close()
        except OSError as why:
            if why.args[0] not in (ENOTCONN, EBADF):
                raise

    # def _send(self, bytes, timeout=-1):
    #     total_sent = 0
    #     msg_len = len(bytes)
    #     # print('Lock acquired')
    #     if self._send_lock.acquire(timeout=timeout):
    #         try:
    #             while total_sent < msg_len:
    #                 sent = self.socket.send(bytes[total_sent:])
    #                 if sent == 0:
    #                     raise RuntimeError('Socket connection broken on send')
    #                 total_sent = total_sent + sent
    #         finally:
    #             self._send_lock.release()
    #
    #         return total_sent
    #     else:
    #         raise RuntimeError('Timed out while sending')


    # def _recv(self, size, fixed=True):
    #     if fixed:
    #         data = bytearray(size)
    #         bytes_recd = 0
    # 
    #         while bytes_recd < size:
    #             to_recv = min(size-bytes_recd, 2048)
    #             chunk = self.socket.recv(to_recv)
    # 
    #             if chunk == b'':
    #                 raise RuntimeError("Client disconnect")
    # 
    #             data[bytes_recd:bytes_recd+to_recv] = chunk
    #             bytes_recd += len(chunk)
    # 
    #         return bytes(data)
    # 
    #     else:
    #         data = self.socket.recv(size)
    #         if data == b'':
    #             raise RuntimeError("Socket connection broken on recv")
    #         return data

    # def send(self, bytes, timeout=-1):
    #     try:
    #         return self._send(bytes, timeout)
    #     except (RuntimeError, socket.error) as e:
    #         self.close(reason=str(e))
    #         raise ConnectionBroken(str(e))

    def recv(self, buffer_size):
        try:
            data = self.socket.recv(buffer_size)
            if not data:
                # a closed connection is indicated by signaling
                # a read condition, and having recv() return 0.
                raise ConnectionClosed('Socket connection closed normally')
            else:
                return data
        except OSError as why:
            # winsock sometimes raises ENOTCONN
            if why.args[0] in _DISCONNECTED:
                raise ConnectionClosed('Socket connection closed ({})'.format(why))
            else:
                raise

    def send(self, data):
        try:
            result = self.socket.send(data)
            return result
        except OSError as why:
            if why.args[0] == EWOULDBLOCK:
                return 0
            elif why.args[0] in _DISCONNECTED:
                raise ConnectionClosed('Socket connection closed ({})'.format(why))
            else:
                raise

class Log:
    INDENTATION = 4

    def __init__(self, *args_):
        self.do = {'errors': False,
                   'enter': False,
                   'exit': False,
                   'args': False}

        for i in args_:
            if i not in self.do and i != 'all':
                print('ERROR:' + i)
                raise ValueError('{} is not a valid variable'.format(i))

        for i in self.do.keys():
            if i in args_ or 'all' in args_:
                self.do[i] = True

    def __call__(self, f):
        def wrapped_f(*args, **kwargs):
            if self.do['enter']:
                logging.debug(self._indent_string(
                             'function {} called with\n'.format(f.__name__) +
                             'args={}\n'.format(args) +
                             'kwargs={}'.format(kwargs), self.INDENTATION))
            try:
                f(*args, **kwargs)
            except:
                if self.do['errors']:
                    logging.error(self._indent_string(
                                  'function {} was called with\n'.format(f.__name__) +
                                  'args={}\n'.format(args) +
                                  'kwargs={}\n'.format(kwargs) +
                                  'and exited with error:\n' +
                                  '-'*50 + '\n' +
                                  logging.traceback.format_exc() +
                                  '-'*50 + '\n', self.INDENTATION))
                raise
            else:
                if self.do['exit']:
                    logging.debug('function {} exited normally'.format(f.__name__))
        return wrapped_f

    @staticmethod
    def _indent_string(string, indentation):
        return (' '*indentation).join(string.splitlines(True))


class SocketServer:

    @Log('errors')
    def __init__(self,
                 port=1234,
                 host=socket.gethostbyname(socket.gethostname()),
                 queue_size=1000,
                 block_time=2,
                 # selector=selectors.EpollSelector,
                 # handle_readable=lambda client: True,
                 # handle_incoming=lambda client: True,
                 # handle_closed=lambda client, reason: True,
                 client_handler=ClientHandler,
                 max_subthreads=-1):

        self.port = port
        self.host = host
        self.queue_size = queue_size
        self.block_time = block_time
        # self.selector = selector
        # self.handle_readable = handle_readable
        # self.handle_incoming = handle_incoming
        # self.handle_closed = handle_closed
        self.client_handler = client_handler

        # self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # self._server_socket.setblocking(False)

        # self._accept_selector = selector()
        # self._recv_selector = selector()

        # server_selector.register(self._server_socket, selectors.EVENT_READ)

        self._loop_objects = (
            loopfunction.Loop(target=self._mainthread_accept_clients,
                              on_start=lambda: logging.info('Thread started: Accept clients'),
                              on_stop=lambda: logging.info('Thread stopped: Accept clients')),

            loopfunction.Loop(target=self._mainthread_poll_readable,
                              on_start=lambda: logging.info('Thread started: Poll for readable clients'),
                              on_stop=lambda: logging.info('Thread stopped: Poll for readable clients')),

        )

        self._threads_limiter = maxthreads.MaxThreads(max_subthreads)
        # self.clients = []

    @Log('errors')
    def _mainthread_accept_clients(self):
        """Accepts new clients and sends them to the to _handle_accepted within a subthread
        """
        try:
            if server_selector.select(timeout=self.block_time):
                # sock, address = self._server_socket.accept()

                # sock.setblocking(False)
                # client = self.client_class(sock, address)
                pair = self.accept()
                if pair is not None:
                    client = self.client_handler()
                    client.socket, client.address = pair
                    client.socket.setblocking(False)
                    self._threads_limiter.start_thread(target=client._handle_socket_accept)

                # client = self.client_handler()  # accepts the new connection and adds client to the list
                # self._threads_limiter.start_thread(target=self._subthread_handle_accepted,
                #                                    args=(client,))

        except socket.error:
            pass

    @Log('errors')
    def _mainthread_poll_readable(self):
        """Searches for readable client sockets. These sockets are then put in a subthread
        to be handled by _handle_readable
        """
        events = clients_selector.select(self.block_time)
        for key, mask in events:
            if mask == selectors.EVENT_READ:
                client = key.fileobj
                client.selector_unregister()
                # self._threads_limiter.start_thread(target=self._subthread_handle_readable,
                #                                    args=(client,))
                self._threads_limiter.start_thread(target=client._handle_socket_message)

    # @Log('errors')
    # def _subthread_handle_accepted(self, client):
    #     """Gets accepted clients from the queue object and sets up the client socket.
    #     The client can then be found in the clients dictionary with the socket object
    #     as the key.
    #     """
    #
    #     try:
    #         # self.handle_incoming(client)
    #         client.handle_socket_accept()
    #     except ConnectionBroken:
    #         pass
    #     else:
    #         if not client.socket_closed:
    #             client.accepted = True
    #             client.selector_register()
    #
    # @Log('errors')
    # def _subthread_handle_readable(self, client):
    #     """Handles readable client sockets. Calls the user modified handle_readable with
    #     the client socket as the only variable. If the handle_readable function returns
    #     true the client is again registered to the selector object otherwise the client
    #     is disconnected.
    #     """
    #     try:
    #         # self.handle_readable(client)
    #         client.handle_socket_message()
    #     except ConnectionBroken:
    #         pass
    #     else:
    #         if not client.socket_closed:
    #             client.selector_register()

    @Log('all')
    def start(self):
        logging.info('Binding server socket to {}:{}'.format(self.host, self.port))
        server_socket.bind((self.host, self.port))

        server_socket.listen(self.queue_size)
        logging.info('Server socket now listening (queue_size={})'.format(self.queue_size))

        logging.info('Starting main threads...')
        for loop_obj in self._loop_objects:
            loop_obj.start()

        logging.info('Main threads started')

    @Log('all')
    def stop(self):
        logging.info('Closing all ({}) connections...'.format(len(clients)))

        for client in clients:
            client.close('Server shutting down')

        # self.close(self.clients, 'Server shutting down')
        logging.info('Stopping main threads...')
        for loop_obj in self._loop_objects:
            loop_obj.send_stop_signal(silent=True)

        for loop_obj in self._loop_objects:
            loop_obj.stop(silent=True)

        logging.info('Shutting down server socket...')
        server_socket.shutdown(socket.SHUT_RDWR)
        logging.info('Closing server socket...')
        server_socket.close()

    @staticmethod
    def clients():
        return clients

    def accept(self):
        """ Returns either an address pair or None
        """
        try:
            conn, addr = server_socket.accept()
        except TypeError:
            return None
        except OSError as why:
            if why.args[0] in (EWOULDBLOCK, ECONNABORTED, EAGAIN):
                return None
            else:
                raise
        else:
            return conn, addr
