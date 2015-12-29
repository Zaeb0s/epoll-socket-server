#!/bin/env python3
import selectors
import queue
import socket
import loopfunction
import logging
import traceback

class SocketServer:

    def log(f):
        def wrapper(*args, **kwargs):
            logging.info('function {} called'.format(f.__name__))
            try:
                f(*args, **kwargs)
            except:
                logging.error('function {} exited with error:\n'.format(f.__name__) +
                              '-'*50 + '\n' +
                              traceback.format_exc() +
                              '-'*50 + '\n')
                raise
            else:
                logging.info('function {} exited normally'.format(f.__name__))
        return wrapper

    @log
    def __init__(self,
                 port=1234,
                 host=socket.gethostbyname(socket.gethostname()),
                 queue_size=1000,
                 block_time=10,
                 selector=selectors.EpollSelector):

        self.port = port
        self.host = host
        self.queue_size = queue_size
        self.block_time = block_time
        self.selector = selector

        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.setblocking(False)

        self._accept_queue = queue.Queue()
        self._recv_queue = queue.Queue()

        self._accept_selector = selector()
        self._recv_selector = selector()

        self._accept_selector.register(self._server_socket, selectors.EVENT_READ)

        self._server1 = loopfunction.Loop(target=self._search_incoming,
                                          on_stop=lambda:
                                          logging.info('search for incoming clients thread stopped'))
        self._server2 = loopfunction.Loop(target=self._search_readable,
                                          on_stop=lambda:
                                          logging.info('search for readable client sockets thread stopped'))
        self._server3 = loopfunction.Loop(target=self._handle_incoming,
                                          on_stop=lambda:
                                          logging.info('handle incoming clients thread stopped'))
        self._server4 = loopfunction.Loop(target=self._handle_readable,
                                          on_stop=lambda:
                                          logging.info('handle readable client sockets thread stopped'))

        self.clients = {}

    def _search_incoming(self):
        if self._accept_selector.select(timeout=self.block_time):
            try:
                client = self._server_socket.accept()
                logging.info('Client connected: {}'.format(client[1]))
                self._accept_queue.put(client)
            except socket.error:
                pass

    def _search_readable(self):
        events = self._recv_selector.select(self.block_time)
        for key, mask in events:
            if mask == selectors.EVENT_READ:
                self._recv_selector.unregister(key.fileobj)
                self._recv_queue.put(key.fileobj)

    def _handle_incoming(self):
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

    def _handle_readable(self):
        try:
            client = self._recv_queue.get(timeout=self.block_time)
            if self.handle_readable(client):
                self.register(client)
            else:
                self.disconnect(client)
        except queue.Empty:
            pass

    def handle_incoming(self, client, address):
        return True

    def handle_readable(self, client):
        return True



    @log
    def start(self):
        logging.info('Binding server socket to {}:{}'.format(self.host, self.port))
        self._server_socket.bind((self.host, self.port))

        self._server_socket.listen(self.queue_size)
        logging.info('Server socket now listening (queue_size={})'.format(self.queue_size))

        logging.info('Starting main threads...')
        self._server1.start(subthread=True)
        logging.info('Now searching for incoming client connections')
        self._server2.start(subthread=True)
        logging.info('Now searching for readable client sockets')
        self._server3.start(subthread=True)
        logging.info('Now handling incoming client connections')
        self._server4.start(subthread=True)
        logging.info('Now handling readable client sockets')
        logging.info('Main threads started')

    @log
    def stop(self):
        logging.info('Closing all ({}) connections...'.format(len(self.clients)))

        self.disconnect(self.clients)
        logging.info('Stopping mainthreads...')
        self._server1.send_stop_signal()
        self._server2.send_stop_signal()
        self._server3.send_stop_signal()
        self._server4.send_stop_signal()
        self._server1.stop()
        self._server2.stop()
        self._server3.stop()
        self._server4.stop()
        logging.info('Closing server socket...')
        self._server_socket.shutdown(socket.SHUT_RDWR)
        self._server_socket.close()

    def register(self, client, silent=False):
        try:
            self._recv_selector.register(client, selectors.EVENT_READ)
        except KeyError:
            if not silent:
                logging.error(
                    'Tried to register an already registered client: {}'.format(self.clients[client]))
                raise KeyError('Client already registered')

    def unregister(self, client, silent=False):
        try:
            self._recv_selector.unregister(client)
        except KeyError:
            if not silent:
                logging.error(
                    'Tried to unregister a client that is not registered: {}'.format(self.clients[client]))
                raise KeyError('Client already registered')

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
