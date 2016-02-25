#!/bin/env python3
import esockets
import threading
import socket
import time
import logging
import sys
from time import sleep
import maxthreads
root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)


class Client:
    def __init__(self, server):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.connect((server.host, server.port))



def handle_incoming(client, address):
    return True


def handle_readable(client):
    data = client.recv(1028)
    print(threading.active_count())
    # print(data)
    if data == b'':
        return False
    return True

server = esockets.SocketServer(handle_incoming=handle_incoming,
                               handle_readable=handle_readable,
                               max_subthreads=100)

server.start()

clients = []
send_threads = maxthreads.MaxThreads(100)

for i in range(200):
    clients.append(Client(server))


def send_from_all(msg):
    for i in clients:
        send_threads.start_thread(target=i.sock.sendall,
                                  args=(msg.encode(),))
# sockets = []
#
# def connect(lock, n):
#     for i in range(n):
#         conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         conn.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         conn.connect((server.host, server.port))
#         sockets.append(conn)
#
#     lock.release()
#
#
# def send():
#     for s in sockets:
#         s.sendall(b'Hello from client!')
#
# def mass_send():
#     while True:
#         send()
#
# def sample(seconds, no_samples):
#     samples = []
#     time1 = time.time()
#     while time.time() - time1 < seconds:
#         t1 = time.time()
#         samples.append(threading.active_count())
#         t2 = time.time() - t1
#         sleep(seconds/no_samples - t2)
#     return samples
#
# conn_lock = threading.Lock()
# conn_lock.acquire()
# threading.Thread(target=connect, args=(conn_lock, 4000)).start()
# conn_lock.acquire()
# threading.Thread(target=mass_send).start()
#
# print('Sampling')
# samples = sample(5, 2000)
# plt.plot(samples)
# plt.show()
