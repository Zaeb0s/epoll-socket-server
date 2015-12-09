#!/bin/env python3
import socket
import threading
import select


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

        self.trigger_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.trigger_client_socket.connect((host, port))
        self.trigger_server_socket, _ = self.server_socket.accept()
        self.client_epoll.register(self.trigger_server_socket.fileno(), select.EPOLLIN)

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
                    try:
                        data = self.clients[fileno].conn.recv(self.BUFFER_SIZE)
                    except socket.error:
                        self.unregister(fileno)

                    if data == b'':
                        self.unregister(fileno)
                    else:
                        self.clients[fileno].recv_buffer.append(data)
                        threading.Thread(target=self.on_message_recv, args=(self.clients[fileno],)).start()

                elif event and select.EPOLLHUP:
                    self.unregister(fileno)

    def unregister(self, fileno):
        self.client_epoll.unregister(fileno)
        threading.Thread(target=self.on_client_disconnect, args=(self.clients[fileno],)).start()

    def start(self):
        """
        Starts the server main loop threads
        """
        threading.Thread(target=self.server_serve_forever).start()
        threading.Thread(target=self.clients_serve_forever).start()
        self.on_start()

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
                    self.clients[conn.fileno()] = conn
                    self.client_epoll.register(conn.fileno(), select.EPOLLIN)

                    threading.Thread(target=self.on_client_connect, args=(conn, )).start()

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
    # --------------------------------------------------------------------------------


class Connection:
    def __init__(self, conn, address):
        self.conn = conn
        self.address = address

        self.recv_buffer = []
        self.send_buffer = []

        self.flushing_send_buffer = False

        self.conn.setblocking(0)

    def fileno(self):
        return self.conn.fileno()

    def close(self):
        return self.conn.close()

    def send(self, data):
        self.send_buffer.append(data)
        if not self.flushing_send_buffer:
            self.flushing_send_buffer = True
            while len(self.send_buffer) != 0:
                frame = self.send_buffer.pop(0)
                total_sent = 0
                to_send = len(frame)
                while total_sent < to_send:
                    sent = self.conn.send(frame[total_sent:])
                    if sent == 0:
                        raise SendError('Could not send some or all of a frame to: %s' % self.getip())
                    else:
                        total_sent += sent
            else:
                self.flushing_send_buffer = False

    def getip(self):
        return '%s:%s' % self.address

class SendError(Exception):
    pass

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
            conn.send(b'hello from server')
            # print(conn.recv_buffer)

        def on_client_disconnect(self, conn):
            # print('Client disconnected')
            del self.clients[conn.fileno()]
            conn.close()


    s = sock(1234)
    s.start()
