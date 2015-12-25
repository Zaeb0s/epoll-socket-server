#!/bin/env python3
import socket
import threading
import selectors
import queue
import errno
from ESocketS.exceptions import *


def send_raw(conn, data, lock=None):

    if lock:
        lock.acquire()
    try:
        to_send, total_sent = len(data), 0
        while total_sent < to_send:
            sent = conn.send(data[total_sent:])
            if sent == 0:
                raise ClientAbnormalDisconnect('Sent empty array')
            total_sent += sent
    except socket.error as e:
        raise ClientAbnormalDisconnect('socket.error while sending ({})'.format(e.args[1]))

    finally:
        if lock:
            lock.release()


def recv_raw(conn, size=4096):
    try:
        data = conn.recv(size)
    except socket.error as e:
        err = e.args[0]
        if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
            # No data in recv buffer
            raise WouldBlock('Tried to read client socket but no data was available')
        else:
            # a "real" error occurred
            raise ClientAbnormalDisconnect('socket.error while receiving ({})'.format(e.args[0]))
    else:
        if data == b'':
            raise ClientDisconnect('Received empty bytes array')
        return data


class _ClientInfo:
    send_lock = threading.Lock()

    def __init__(self, address, callback_function, callback_args):
        self.address = address
        self.callback_function = callback_function
        self.callback_args = callback_args


class Socket:
    def __init__(self,
                 port=1234,
                 host=socket.gethostbyname(socket.gethostname()),
                 queue_size=1000,
                 block_time=2,
                 selector=selectors.PollSelector()):

        self.host = host
        self.port = port
        self.queue_size = queue_size
        self.block_time = block_time
        self._epoll = selector

        self._run_in_subthread = {self.on_poll.__name__: False,
                                  self.on_connect.__name__: False,
                                  self.on_start.__name__: False,
                                  self.on_stop.__name__: False,
                                  'client_callback': True}

        self._serve_threads = {'_recv': threading.Thread(target=self._recv),
                               '_accept': threading.Thread(target=self._accept),
                               '_handle_connects': threading.Thread(target=self._handle_connects)}

        self._stop_events = {'_recv': threading.Event(),
                             '_accept': threading.Event(),
                             '_handle_connects': threading.Event()}

        self.clients = {}

        self._started = False
        self._stop_signal = False

        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.setblocking(False)

        self._accept_queue = queue.Queue()

    # ------------ private functions --------------
    def _recv(self):
        try:
            while not self._stop_signal:
                events = self._epoll.select(self.block_time)
                for key, mask in events:
                    self.unregister(key.fileobj)
                    self._call_on_function(self.on_poll, (key.fileobj, ))

        finally:
            self._stop_events['_recv'].set()
            if not self._stop_signal:
                # Error occurred
                self.stop('Error in _recv')

    def _accept(self):
        server_epoll = selectors.EpollSelector()
        server_epoll.register(self._server_socket, selectors.EVENT_READ)
        try:
            while not self._stop_signal:
                server_epoll.select(self.block_time)
                try:
                    conn, address = self._server_socket.accept()
                    self._accept_queue.put((conn, address))

                except BlockingIOError:
                    pass
        finally:
            self._stop_events['_accept'].set()
            if not self._stop_signal:
                # Error occurred
                self.stop('Error in _accept')

    def _handle_connects(self):
        try:
            while not self._stop_signal:
                try:
                    conn, address = self._accept_queue.get(timeout=self.block_time)
                except queue.Empty:
                    pass
                else:
                    conn.setblocking(False)

                    client = _ClientInfo(address, self.recv, (conn, ))

                    self.clients[conn] = client
                    self._call_on_function(self.on_connect, (conn, ))

        finally:
            self._stop_events['_handle_connects'].set()
            if not self._stop_signal:
                # Error occured
                self.stop('Error in _handle_connects')

    def _handle_poll(self, conn):
        if self.on_poll(conn):
            self.register(conn)

    # ---------------------------------------------

    # -------------- user interface ---------------
    # These functions need to have good error handling
    # Throwing errors where necessary

    # get_ip
    # get_clients
    # unregister
    # register
    # start
    # stop
    # disconnect

    def register(self, conn, silent=False):
        client = self.clients[conn]
        if silent:
            try:
                self._epoll.register(conn, selectors.EVENT_READ,
                                     (client.callback_function, client.callback_args))
            except KeyError:
                pass
        else:
            self._epoll.register(conn, selectors.EVENT_READ,
                                 (client.callback_function, client.callback_args))

    def unregister(self, conn, silent=False):
        try:
            self._epoll.unregister(conn)
        except KeyError:
            if not silent:
                raise KeyError('Client not registered')

    def start(self):
        if self._started:
            raise OSError('Server can only be started once')
        self._started = True
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen(self.queue_size)

        for thread in self._serve_threads.values():
            thread.start()

        self._call_on_function(self.on_start, ())

    def stop(self, reason=''):
        if not self._started:
            raise OSError("Can't stop server because it has not been started yet")

        if self._stop_signal:
            raise OSError('Server has already been stopped')

        self._stop_signal = True

        self.disconnect('all')

        # Waiting for the serve forever threads to stop
        for event in self._stop_events.values():
            event.wait()

        self._server_socket.shutdown(0)
        self._server_socket.close()
        self._call_on_function(self.on_stop, (reason,))

    def restart(self):
        try:
            self.stop()
        except OSError:
            pass
        self.__init__(port=self.port,
                      host=self.host,
                      queue_size=self.queue_size,
                      block_time=self.block_time)

        self.start()

    def disconnect(self, conn):

        if conn == 'all':
            clients = self.clients.keys()
        else:
            clients = [conn]

        for client in clients:
            self.unregister(client, silent=True)
            try:
                client.shutdown(socket.SHUT_RDWR)
            except socket.error:
                pass
            client.close()

        if conn == 'all':
            self.clients.clear()
        else:
            del self.clients[conn]

    def run_in_subthread(self, function, yes_no):
        if hasattr(function, __name__) and function.__name__ in self._run_in_subthread:
            key = function.__name__
        elif type(function) == str and (function in self._run_in_subthread or function == 'all'):
            key = function
        else:
            raise ValueError('The function is not a valid option')

        if yes_no:
            choice = True
        else:
            choice = False

        if key == 'all':
            for i in self._run_in_subthread:
                self._run_in_subthread[i] = choice
        else:
            self._run_in_subthread[key] = choice

    def get_ip(self, conn):
        return self.clients[conn].address

    def recv(self, conn, size=4096):
        return recv_raw(conn, size)

    def send(self, conn, data, block=True):
        if block:
            send_raw(conn, data, self.clients[conn].send_lock)
        else:
            send_raw(conn, data)

    def get_clients(self):
        """ Returns a generator object containing all clients
        """
        return (i for i in self.clients)

    # ---------------------------------------------

    # ---------------------------- the "on" functions --------------------------------
    def _call_on_function(self, on_function, args):
        if self._run_in_subthread[on_function.__name__]:
            threading.Thread(target=on_function, args=args).start()
        else:
            on_function(*args)

    def on_start(self):
        pass

    def on_stop(self, reason):
        pass

    def on_poll(self, conn):
        pass

    def on_connect(self, conn):
        pass


    # --------------------------------------------------------------------------------
