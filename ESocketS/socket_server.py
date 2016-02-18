#!/bin/env python3
import selectors
import socket
import loopfunction
import logging
import threading
import queue
import maxthreads
from time import sleep

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
                logging.debug(indent_string(
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
                    logging.debug('function {} exited normally'.format(f.__name__))
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
                 handle_incoming=lambda: True,
                 max_subthreads=-1):

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

        self._accept_selector = selector()
        self._recv_selector = selector()

        self._accept_selector.register(self._server_socket, selectors.EVENT_READ)

        self._loop_objects = (
            loopfunction.Loop(target=self._mainthread_accept_clients,
                              on_start=lambda: logging.debug('Thread started: Accept clients'),
                              on_stop=lambda: logging.debug('Thread stopped: Accept clients')),

            loopfunction.Loop(target=self._mainthread_poll_readable,
                              on_start=lambda: logging.debug('Thread started: Poll for readable clients'),
                              on_stop=lambda: logging.debug('Thread stopped: Poll for readable clients')),
        )
        self.max_subthreads = max_subthreads
        if max_subthreads > 0:
            self._loop_objects += (loopfunction.Loop(target=self._mainthread_start_subfunctions,
                                   on_start=lambda: logging.debug('Thread started: Start sub-functions'
                                                                  ' (maximum subthreads: {})'.format(max_subthreads)),
                                   on_stop=lambda: logging.debug('Thread stopped: Start sub-functions')),)
            self._maxSub = maxthreads.MaxThreads(max_subthreads)
            self._sub_functions_queue = queue.Queue()
            self._max_subthreads_lock = threading.BoundedSemaphore(max_subthreads)
        self.clients = {}

    @Log('errors')
    def _mainthread_accept_clients(self):
        """Accepts new clients and sends them to the to _handle_accepted within a subthread
        """
        try:
            if self._accept_selector.select(timeout=self.block_time):
                client = self._server_socket.accept()
                logging.info('Client connected: {}'.format(client[1]))

                # self._start_subthread(target=self._subthread_handle_accepted, args=(client,))
                self._start_subthread(target=self._subthread_handle_accepted,
                                      args=(client,))
                # self._sub_functions_queue.put((self._subthread_handle_accepted, (client,), {}))
        except socket.error:
            pass

    @Log('errors')
    def _mainthread_poll_readable(self):
        """Searches for readable client sockets. These sockets are then put in a subthread
        to be handled by _handle_readable
        """
        events = self._recv_selector.select(self.block_time)
        for key, mask in events:
            if mask == selectors.EVENT_READ:
                self._recv_selector.unregister(key.fileobj)
                # self._start_subthread(target=self._subthread_handle_readable, args=(key.fileobj,))
                # self._sub_functions_queue.put((self._subthread_handle_readable, (key.fileobj,), {}))
                self._start_subthread(target=self._subthread_handle_readable,
                                      args=(key.fileobj,))

    @Log('errors')
    def _mainthread_start_subfunctions(self):
        # sleep(0.2)
        try:
            target, args, kwargs = self._sub_functions_queue.get(timeout=self.block_time)
        except queue.Empty:
            pass
        else:
            # self._maxSub.start_thread(target, args, kwargs)
            print('Threads: ', threading.active_count())
            self._max_subthreads_lock.acquire()
            threading.Thread(target=target,
                             args=args,
                             kwargs=kwargs).start()

    @Log('errors')
    def _subthread_handle_accepted(self, client):
        """Gets accepted clients from the queue object and sets up the client socket.
        The client can then be found in the clients dictionary with the socket object
        as the key.
        """
        try:
            conn, addr = client
            if self.handle_incoming(conn, addr):
                logging.info('Accepted connection from client: {}'.format(addr))
                conn.setblocking(False)
                self.clients[conn] = addr
                self.register(conn)
            else:
                logging.info('Refused connection from client: {}'.format(addr))
                self.disconnect(conn)
        finally:
            if self.max_subthreads > 0:
                self._max_subthreads_lock.release()

    @Log('errors')
    def _subthread_handle_readable(self, conn):
        """Handles readable client sockets. Calls the user modified handle_readable with
        the client socket as the only variable. If the handle_readable function returns
        true the client is again registered to the selector object otherwise the client
        is disconnected.
        """
        try:
            if self.handle_readable(conn):
                self.register(conn)
            else:
                self.disconnect(conn)
        finally:
            if self.max_subthreads > 0:
                self._max_subthreads_lock.release()

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

    def _start_subthread(self, target, args=(), kwargs={}):
        if self.max_subthreads > 0:
            self._sub_functions_queue.put((target, args, kwargs))
        else:
            threading.Thread(target=target,
                             args=args,
                             kwargs=kwargs).start()
            print('Threads: ', threading.active_count())

