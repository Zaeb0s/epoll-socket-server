#!/bin/env python3
import ESocketS
import threading
import socket
import time

class EchoServer(ESocketS.SocketServer):
    clients = {}

    def handle_incoming(self, client, address):
        # print(address, 'Connected')
        self.clients[client] = address
        self.register(client)

    def handle_readable(self, client):
        data = client.recv(1028)
        if data == b'':
            print(client.getpeername(), 'Disconnected')
            return

        print(client.getpeername(), data)
        self.register(client)
        client.sendall(b'SERVER: ' + data)


s = EchoServer()
s.start()

# clients = []
# sent = 0

class temp:
    clients = []
    sent = 0

def connect_clients(no_clients):
    t1 = time.time()
    for i in range(no_clients):
        threading.Thread(target=connect).start()
    while len(temp.clients) != no_clients:
        pass
    return time.time() - t1


def send_from_all(message):
    temp.sent = 0
    t1 = time.time()
    for i in temp.clients:
        threading.Thread(target=send, args=(i, message)).start()
    while temp.sent != len(temp.clients):
        pass
    return time.time() - t1

def connect():
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    conn.connect((s.host, s.port))
    temp.clients.append(conn)

def send(client, msg):
    client.sendall(msg)
    temp.sent += 1