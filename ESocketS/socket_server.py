#!/bin/env python3
import selectors
import queue
import socket
import loopfunction
import logging


def indent_string(string, indentation):
    return (' '*indentation).join(string.splitlines(True))


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
                logging.info(indent_string(
                             'function {} called with\n'.format(f.__name__) +
                             'args={}\n'.format(args) +
                             'kwargs={}'.format(kwargs), self.INDENTATION))
            try:
                f(*args, **kwargs)
            except:
                if self.do['errors']:
                    logging.error(indent_string(
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
                    logging.info('function {} exited normally'.format(f.__name__))
        return wrapped_f


class SocketServer:

    @Log('errors')
    def __init__(self,
                 port=1234,
                 host=socket.gethostbyname(socket.gethostname()),
                 queue_size=1000,
                 block_time=2,
                 selector=selectors.EpollSelector,
                 handle_readable=lambda: True,
                 handle_incoming=lambda: True):

        self.port = port
        self.host = host
        self.queue_size = queue_size
        self.block_time = block_time
        self.selector = selector
        self.handle_readable = handle_readable
        self.handle_incoming = handle_incoming

        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.setblocking(False)

        self._accept_queue = queue.Queue()
        self._recv_queue = queue.Queue()

        self._accept_selector = selector()
        self._recv_selector = selector()

        self._accept_selector.register(self._server_socket, selectors.EVENT_READ)

        self._loop_objects = (
            loopfunction.Loop(target=self._accept_clients,
                              on_start=lambda: logging.info('Thread started: Accept clients'),
                              on_stop=lambda: logging.info('Thread stopped: Accept clients')),

            loopfunction.Loop(target=self._poll_readable,
                              on_start=lambda: logging.info('Thread started: Poll for readable clients'),
                              on_stop=lambda: logging.info('Thread stopped: Poll for readable clients')),

            loopfunction.Loop(target=self._handle_accepted,
                              on_start=lambda: logging.info('Thread started: Handle accepted clients'),
                              on_stop=lambda: logging.info('Thread stopped: Handle accepted clients')),

            loopfunction.Loop(target=self._handle_readable,
                              on_start=lambda: logging.info('Thread started: Handle readable clients'),
                              on_stop=lambda: logging.info('Thread stopped: Handle readable clients')),
        )
        self.clients = {}

    @Log('errors')
    def _accept_clients(self):
        """Accepts new clients and sends them to the _accept_queue to be handled by _handle_accepted
        """
        try:
            if self._accept_selector.select(timeout=self.block_time):
                client = self._server_socket.accept()
                logging.info('Client connected: {}'.format(client[1]))
                self._accept_queue.put(client)
        except socket.error:
            pass

    @Log('errors')
    def _handle_accepted(self):
        """Gets accepted clients from the queue object and sets up the client socket.
        The client can then be found in the clients dictionary with the socket object
        as the key.
        """
        try:
            client, address = self._accept_queue.get(timeout=self.block_time)
            if self.handle_incoming(client, address):
                logging.info('Accepted connection from client: {}'.format(address))
                client.setblocking(False)
                self.clients[client] = address
                self.register(client)
            else:
                logging.info('Refused connection from client: {}'.format(address))
                self.disconnect(client)
        except queue.Empty:
            pass

    @Log('errors')
    def _poll_readable(self):
        """Searches for readable client sockets. These sockets are then put in a queue
        to be handled by _handle_readable
        """
        events = self._recv_selector.select(self.block_time)
        for key, mask in events:
            if mask == selectors.EVENT_READ:
                self._recv_selector.unregister(key.fileobj)
                self._recv_queue.put(key.fileobj)

    @Log('errors')
    def _handle_readable(self):
        """Handles readable client sockets. Calls the user modified handle_readable with
        the client socket as the only variable. If the handle_readable function returns
        true the client is again registered to the selector object otherwise the client
        is disconnected.
        """
        try:
            client = self._recv_queue.get(timeout=self.block_time)
            if self.handle_readable(client):
                self.register(client)
            else:
                self.disconnect(client)
        except queue.Empty:
            pass

    @Log('all')
    def start(self):
        logging.info('Binding server socket to {}:{}'.format(self.host, self.port))
        self._server_socket.bind((self.host, self.port))

        self._server_socket.listen(self.queue_size)
        logging.info('Server socket now listening (queue_size={})'.format(self.queue_size))

        logging.info('Starting main threads...')
        for loop_obj in self._loop_objects:
            loop_obj.start()

        logging.info('Main threads started')

    @Log('all')
    def stop(self):
        logging.info('Closing all ({}) connections...'.format(len(self.clients)))

        self.disconnect(self.clients)
        logging.info('Stopping main threads...')
        for loop_obj in self._loop_objects:
            loop_obj.send_stop_signal(silent=True)

        for loop_obj in self._loop_objects:
            loop_obj.stop(silent=True)

        logging.info('Shutting down server socket...')
        self._server_socket.shutdown(socket.SHUT_RDWR)
        logging.info('Closing server socket...')
        self._server_socket.close()

    @Log('errors')
    def register(self, client, silent=False):
        try:
            self._recv_selector.register(client, selectors.EVENT_READ)
        except KeyError:
            if not silent:
                logging.error(
                    'Tried to register an already registered client: {}'.format(self.clients[client]))
                raise KeyError('Client already registered')

    @Log('errors')
    def unregister(self, client, silent=False):
        try:
            self._recv_selector.unregister(client)
        except KeyError:
            if not silent:
                logging.error(
                    'Tried to unregister a client that is not registered: {}'.format(self.clients[client]))
                raise KeyError('Client already registered')

    @Log('errors')
    def disconnect(self, client, how=socket.SHUT_RDWR):
        if hasattr(client, '__iter__'):
            if client == self.clients:
                client = self.clients.copy()
            for i in client:
                self.disconnect(i, how)

        else:
            self.unregister(client, True)
            address = 'Could not find address'
            try:
                address = client.getpeername()
                client.shutdown(socket.SHUT_RDWR)
            except socket.error:
                pass
            client.close()

            try:
                address = self.clients[client]
                del self.clients[client]
            except KeyError:
                pass
            logging.info('Client disconnected: {}'.format(address))
