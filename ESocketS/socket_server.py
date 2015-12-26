#!/bin/env python3
import selectors
import queue
import socket
import threading


class _ServeForever:
    """Polls for new clients then accepts and puts them into the clients queue.Queue object
    server_socket is a bound and listening socket.socket object
    """

    def __init__(self, function, *args, **kwargs):

        self.function = function
        self.args = args
        self.kwargs = kwargs

        self._stop_signal = False

        self._lock = threading.Event()
        self._lock.set()

    def _loop(self):
        self._lock.clear()
        try:
            while not self._stop_signal:
                self.function(*self.args, **self.kwargs)

        finally:
            self._lock.set()

    def start(self):
        if self.is_running():
            raise RuntimeError('Mainloop is already running')
        else:
            self._stop_signal = False
            self._loop()

    def stop(self):
        self._stop_signal = True
        self._lock.wait()

    def send_stop_signal(self):
        self._stop_signal = True

    def restart(self):
        self.stop()
        self.__init__(self.function, *self.args, **self.kwargs)
        self.start()

    def is_running(self):
        return not self._lock.is_set()


class SocketServer:
    def __init__(self,
                 port=1234,
                 host=socket.gethostbyname(socket.gethostname()),
                 queue_size=1000,
                 block_time=10,
                 selector=selectors.EpollSelector):

        self.port = port
        self.host = socket.gethostbyname(socket.gethostname())
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

        self._server1 = _ServeForever(self._search_incoming)
        self._server2 = _ServeForever(self._search_readable)
        self._server3 = _ServeForever(self._handle_incoming)
        self._server4 = _ServeForever(self._handle_readable)

    def _search_incoming(self):
        if self._accept_selector.select(timeout=self.block_time):
            try:
                client = self._server_socket.accept()
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
            client.setblocking(False)
            self.handle_incoming(client, address)
        except queue.Empty:
            pass

    def _handle_readable(self):
        try:
            client = self._recv_queue.get(timeout=self.block_time)
            self.handle_readable(client)
        except queue.Empty:
            pass

    def handle_readable(self, client):
        pass

    def handle_incoming(self, client, address):
        pass

    def start(self):
        try:
            self._server_socket.bind((self.host, self.port))
        except OSError:
            pass
        self._server_socket.listen(self.queue_size)

        threading.Thread(target=self._server1.start).start()
        threading.Thread(target=self._server2.start).start()
        threading.Thread(target=self._server3.start).start()
        threading.Thread(target=self._server4.start).start()

    def stop(self):
        self._server1.send_stop_signal()
        self._server2.send_stop_signal()
        self._server3.send_stop_signal()
        self._server4.send_stop_signal()

        self._server1.stop()
        self._server2.stop()
        self._server3.stop()
        self._server4.stop()

    def register(self, client):
        self._recv_selector.register(client, selectors.EVENT_READ)


# class AcceptServer:
#     def __init__(self,
#                  server_socket,
#                  block_time=2,
#                  selector=selectors.PollSelector):
#
#         self.server_socket = server_socket
#         self.block_time = block_time
#         self.selector = selector()
#
#         self.server = ServeForever(self.accept, self)
#         self.selector.register(server_socket, selectors.EVENT_READ)
#         self._queue = queue.Queue()
#
#     def accept(self):
#         if self.selector.select(self.block_time):
#             try:
#                 client = self.server_socket.accept()
#             except socket.error:
#                 pass
#             else:
#                 self._queue.put(client)
#             finally:
#                 self.server.stop()
#
#     def get(self, timeout):
#         return self._queue.get(timeout=timeout)
#
#
# class RecvServer(ServeForever):
#     def __init__(self,
#                  block_time=2,
#                  selector=selectors.PollSelector):
#
#         self.block_time = block_time
#         self.selector = selector()
#
#         ServeForever.__init__(self)
#
#         self._queue = queue.Queue()
#
#     def loop_function(self):
#         events = self.selector.select(self.block_time)
#         for key, mask in events:
#             self.selector.unregister(key.fileobj)
#             self._queue.put(key.fileobj)
#
#     def get(self, timeout):
#         return self._queue.get(timeout=timeout)
#
#
#
# class handleQueue(ServeForever):
#     def __init__(self,
#                  thequeue,
#                  block_time=2):
#
#         self.block_time = block_time
#
#         ServeForever.__init__(self)
#
#         self._queue = thequeue
#
#     def loop_function(self):
#         data = self._queue.get(timeout=self.block_time)
#
#
#
# class SocketServer:
#     def __init__(self,
#                  port=1234,
#                  host=socket.gethostbyname(socket.gethostname()),
#                  queue_size=1000,
#                  block_time=2,
#                  selector=selectors.PollSelector):
#
#         self.host = host
#         self.port = port
#         self.queue_size = queue_size
#
#         self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         self._server_socket.setblocking(False)
#
#         self._accept_server = AcceptServer(self._server_socket,
#                                           block_time,
#                                           selector)
#
#         self._recv_server = RecvServer(block_time,
#                                       selector)
#
#     def register(self, client):
#         self._recv_server.selector.register(client, selectors.EVENT_READ)
#
#     def unregister(self, client):
#         self._recv_server.selector.unregister(client)
#
#     def start(self):
#         self._accept_server.start()
#         self._recv_server.start()
#
#     def _handle_recv(self):
#         try:
#
#     def handle_recv(self):
#         pass
#
#     def handle_accept(self):
#         pass
#
#
# class NormalStop(Exception):
#     pass
#
# class ErrorStop(Exception):
#     pass