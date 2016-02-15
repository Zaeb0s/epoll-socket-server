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

# def handle_incoming(client, address):
#     client.sendall(b'SERVER: Connection accepted!\n')
#     return True
#
# def handle_readable(client):
#     data = client.recv(1028)
#     if data == b'':
#         return False
#     client.sendall(b'SERVER: ' + data)
#     return True
#
# server = ESocketS.SocketServer(handle_incoming=handle_incoming,
#                                handle_readable=handle_readable)
# server.start()
# print('Server started on: {}:{}'.format(server.host, server.port))

def handle_incoming(client, address):
    return True


def handle_readable(client):
    data = client.recv(1028)
    if data == b'':
        return False

    for i in server.clients:
        i.sendall('{}: {}'.format(server.clients[i], data).encode() + b'\n')
    print(server.clients[client], data)
    return True

server = ESocketS.SocketServer(handle_incoming=handle_incoming,
                               handle_readable=handle_readable)



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
    conn.connect((server.host, server.port))
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