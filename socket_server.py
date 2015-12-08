#!/bin/env python3
import socket
import threading
import select


class Socket:
    def __init__(self, port, host=socket.gethostbyname(socket.gethostname()), buffer_size=2048, client_timeout=10, server_timeout=1):
        # If no host is given the server is hosted on the local ip

        # Starting the server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.settimeout(server_timeout)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)

        self.trigger_select_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.trigger_select_socket.connect((host, port))
        conn, addr = self.server_socket.accept()

        self.host = host
        self.port = port
        self.serve = True
        self.buffer_size = buffer_size
        self.clients = [Connection(conn, addr, 0.1)]
        self.ready_clients = [self.clients[0]]
        self.client_timeout = client_timeout

    def start(self):
        """
        Starts the server main loop threads
        """
        threading.Thread(target=self.server_thread).start()
        threading.Thread(target=self.clients_thread).start()
        self.on_start()

    def server_thread(self):
        """
        Handles new incoming connections
        """
        while self.serve:
            # Pauses the thread until a new incoming connection is detected
            r_list, _, _ = select.select((self.server_socket,), (), ())
            try:
                conn, addr = self.server_socket.accept()
                threading.Thread(target=self.new_client, args=(conn, addr)).start()
            except socket.timeout:
                print('TImed out')

    def new_client(self, conn, addr):
        connection = Connection(conn, addr, self.client_timeout)
        self.clients.append(connection)
        self.ready_clients.append(connection)
        self.trigger_client_thread()
        self.on_client_connect(connection)

    def clients_thread(self):
        """
        Handles new incoming messages from clients
        """
        while self.serve:
            r_list, _, _ = select.select(self.ready_clients, (), ())
            # print('client thread triggered')
            for conn in r_list:
                if conn == self.clients[0]:
                    conn.conn.recv(1)
                else:
                    self.ready_clients.remove(conn)
                    threading.Thread(target=self.new_msg, args=(conn,)).start()

    def new_msg(self, conn):
        try:
            message = conn.recv(self.buffer_size)
        except ValueError:
            # Closing connection on receiving empty array
            self.close_connection(conn)
            return

        self.on_message_recv(conn)

        if conn in self.clients:
            self.ready_clients.append(conn)
            self.trigger_client_thread()


    def trigger_client_thread(self):
        # When the self.ready_connections list has changed the select.select
        # function needs to be triggered in order to register the changes
        # This is a bit ugly but I think it is efficient enough to work well
        self.trigger_select_socket.send(b'0')

    def close_connection(self, conn):
        self.before_close_connection(conn)
        try:
            self.ready_clients.remove(conn)
        except ValueError:
            pass

        try:
            self.clients.remove(conn)
        except ValueError:
            pass

        self.trigger_client_thread()

        try:
            conn.conn.shutdown(1)
        except:
            pass

        conn.conn.close()

    # ---------------------------- the "on" functions --------------------------------
    def on_client_connect(self, client):
        pass

    def on_incoming_message(self, client):
        # Here the user is expected to empty the receiving buffer from the client
        pass

    def on_start(self):
        pass

    def on_message_recv(self, conn):
        # Triggers when server receives a message from the client
        # The message can be found in conn.recv_buffer where each
        # message up to self.buffer_size is stored in a list
        pass

    def before_close_connection(self, conn):
        pass
    # --------------------------------------------------------------------------------


class Connection:
    def __init__(self, conn, address, timeout=10.0):
        self.conn = conn
        self.address = address

        self.conn.settimeout(timeout)
        self.recv_buffer = []
        self.send_buffer = []

        self.flushing_send_buffer = False

    def fileno(self):
        return self.conn.fileno()

    def recv(self, buffer_size):
        data = self.conn.recv(buffer_size)
        if data == b'':
            raise ValueError('Received empty byte array from client')
        else:
            self.recv_buffer.append(data)

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
                        raise ValueError('Zero bytes sent to client')
                    else:
                        total_sent += sent
            else:
                self.flushing_send_buffer = False




if __name__ == '__main__':
    class sock(Socket):
        def __init__(self, port):
            Socket.__init__(self, port)

        def on_client_connect(self, client):
            # print('Client connected')
            pass

        def on_start(self):
            print('Server started: ', self.host, ':', self.port)

        def on_message_recv(self, conn):
            for i in self.clients[1:]:
                i.send(conn.recv_buffer[-1])
            pass

        def before_close_connection(self, conn):
            print('Closing connection')

    s = sock(1234)
    s.start()
