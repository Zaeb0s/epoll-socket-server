#!/bin/env python3
import socket
import threading
import select
from connection import Connection
from action_signal import Action
from bytes_convert import bytes2int
from time import sleep, time
import errno

class Socket:
    def __init__(self,
                 port=1234,
                 host=socket.gethostbyname(socket.gethostname()),
                 BUFFER_SIZE=2048,
                 QUEUE_SIZE=100,
                 SERVER_EPOLL_BLOCK_TIME=10,
                 CLIENT_EPOLL_BLOCK_TIME=1 ):
        # If no host is given the server is hosted on the local ip

        # Starting the server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen(QUEUE_SIZE)
        self.server_socket.setblocking(0)

        self.server_epoll = select.epoll()
        self.server_epoll.register(self.server_socket.fileno(), select.EPOLLIN)

        self.client_epoll = select.epoll()

        self.clients = {}

        self.AS = Action(host, port)
        self.AS.connect()
        self.ASS, _ = self.server_socket.accept()
        self.client_epoll.register(self.ASS.fileno(), select.EPOLLIN)

        self.serve = True

        self.host = host
        self.port = port

        self.BUFFER_SIZE = BUFFER_SIZE
        self.SERVER_EPOLL_BLOCK_TIME = SERVER_EPOLL_BLOCK_TIME
        self.CLIENT_EPOLL_BLOCK_TIME = CLIENT_EPOLL_BLOCK_TIME

    def clients_serve_forever(self):
        while self.serve:
            events = self.client_epoll.poll(self.CLIENT_EPOLL_BLOCK_TIME)
            for fileno, event in events:
                if event == select.EPOLLIN:
                    if fileno == self.ASS.fileno():
                        # The server has sent an action signal to the epoll loop
                        self.handle_action_signal(self.ASS.recv(1))
                    else:
                        try:
                            data = self.clients[fileno].conn.recv(self.BUFFER_SIZE)
                        except socket.error as e:
                            if e.args[0] not in (errno.EWOULDBLOCK, errno.EAGAIN):
                                # since this is a non-blocking socket.
                                self.unregister(fileno)
                            continue

                        if data == b'':
                            self.unregister(fileno)
                        else:
                            self.clients[fileno].recv_buffer.append(data)
                            threading.Thread(target=self.on_message_recv, args=(self.clients[fileno],)).start()

                elif event & (select.EPOLLERR | select.EPOLLHUP):
                    self.unregister(fileno)

    def unregister(self, fileno):
        try:
            self.client_epoll.unregister(fileno)
            threading.Thread(target=self.on_client_disconnect, args=(self.clients[fileno],)).start()
        except FileNotFoundError:
            self.on_warning('Failed to remove: %s because client not registered in the epoll object' % conn.getip())

    def register(self, fileno):
        self.client_epoll.register(fileno, select.EPOLLIN)
        threading.Thread(target=self.on_client_connect, args=(self.clients[fileno],)).start()

    # the add and remove client functions are the two functions used to handle connections
    # outside the client_serve_forever loop
    # conn is the Connection object
    def add_client(self, conn):
        self.clients[conn.fileno()] = conn
        self.AS.send(self.AS.ADD_CLIENT, conn.fileno())

    def remove_client(self, conn, send_action_signal=True):
        fno = conn.fileno()
        if send_action_signal:
            self.AS.send(self.AS.REMOVE_CLIENT, fno)
        self.shutdown_connection(conn)
        try:
            del self.clients[fno]
        except KeyError:
            self.on_warning('Failed to remove: %s client not found in clients dict' % conn.getip())

    @staticmethod
    def shutdown_connection(conn):
        try:
            conn.shutdown(socket.SHUT_RDWR)
        except socket.error:
            pass
        conn.close()

    def handle_action_signal(self, signal):
        frame = self.ASS.recv(signal[0])
        if frame[0:1] == self.AS.ADD_CLIENT:
            self.register(bytes2int(frame[1:]))
        elif frame[0:1] == self.AS.REMOVE_CLIENT:
            self.unregister(bytes2int(frame[1:]))

    def start(self):
        """
        Starts the server main loop threads
        """
        threading.Thread(target=self.server_serve_forever).start()
        threading.Thread(target=self.clients_serve_forever).start()
        self.on_start()

    def stop(self):
        self.on_server_shutting_down()
        self.serve = False
        t1 = time()
        self.client_epoll.close()
        self.server_epoll.close()

        for i in self.clients:
            self.remove_client(self.clients[i], send_action_signal=False)

        t = max(self.CLIENT_EPOLL_BLOCK_TIME, self.SERVER_EPOLL_BLOCK_TIME) - (time()-t1)
        if t > 0:
            sleep(t)

        self.server_socket.close()



        sleep(max(self.CLIENT_EPOLL_BLOCK_TIME, self.SERVER_EPOLL_BLOCK_TIME))
        self.on_server_shut_down()

    def server_serve_forever(self):
        """
        Handles new incoming connections
        """
        while self.serve:
            events = self.server_epoll.poll(self.SERVER_EPOLL_BLOCK_TIME)
            for event, fileno in events:
                if event:
                    conn, addr = self.server_socket.accept()
                    conn = Connection(conn, addr)
                    self.add_client(conn)

    # ---------------------------- the "on" functions --------------------------------
    def on_client_connect(self, conn):
        pass

    def on_start(self):
        pass

    def on_message_recv(self, conn):
        # Triggers when server receives a message from the client
        # The message can be found in conn.recv_buffer where each
        # messages up to self.buffer_size is stored in a list
        pass

    def on_client_disconnect(self, conn):
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
        def __init__(self, port):
            Socket.__init__(self, port)

        def on_start(self):
            print('Server started on: ', self.host, self.port)

        def on_client_connect(self, conn):
            # print(conn.getip(), 'Connected')
            pass

        def on_message_recv(self, conn):
            conn.send(b'hello from server\n')
            # print(conn.recv_buffer)

        def on_client_disconnect(self, conn):
            # print('Client disconnected')
            del self.clients[conn.fileno()]
            conn.close()

        def on_server_shutting_down(self):
            print('Server shutting down')

        def on_server_shut_down(self):
            print('Server is now closed')

    s = sock(1234)
    s.start()
