#!/bin/env python3
import ESocketS
import threading
import socket
import time
import logging
import sys

root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)


class EchoServer(ESocketS.SocketServer):

    def handle_incoming(self, client, address):
        return True

    def handle_readable(self, client):
        data = client.recv(1028)
        if data == b'':
            return False

        print(self.clients[client], data)
        client.sendall(b'SERVER: ' + data)
        return True

s = EchoServer()
# s.start()

# clients = []
# sent = 0

class temp:
    clients = []
    sent = 0

def connect_clients(no_clients):
    t1 = time.time()
    for i in range(no_clients):
        threading.Thread(target=connect).start()
    # while len(temp.clients) != no_clients:
    #     pass
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
    conn.sendall(b'hej '*500)
    conn.shutdown(socket.SHUT_RDWR)
    conn.close()
    # temp.clients.append(conn)

def send(client, msg):
    client.sendall(msg)
    temp.sent += 1

#
# class logg:
#     def __init__(self, f):
#         self.f = f
#
#     def __call__(self, *args, **kwargs):
#         logging.info('function {} called'.format(self.f.__name__))
#         self.f(*args, **kwargs)
#         logging.info('function {} exited'.format(self.f.__name__))
#
#
# @logg
# def party():
#     print('hi')