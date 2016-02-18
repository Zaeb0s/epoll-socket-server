#!/bin/env python3
import ESocketS
import threading
import socket
import time
import logging
import sys
import matplotlib

root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.CRITICAL)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)


def handle_incoming(client, address):
    return True


def handle_readable(client):
    data = client.recv(1028)
    if data == b'':
        return False

    # j = 0
    # while j < len(server.clients):
    #     i = list(server.clients)[j]
    #     i.sendall('{}: {}'.format(server.clients[i], data).encode() + b'\n')
    #     j += 1
    # print(server.clients[client], data)
    return True

server = ESocketS.SocketServer(handle_incoming=handle_incoming,
                               handle_readable=handle_readable,
                               max_subthreads=-4)




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
    time.sleep(0.2)
    # conn.sendall(b'hej \n')
    # conn.shutdown(socket.SHUT_RDWR)
    # conn.close()
    temp.clients.append(conn)

def send(client, msg):
    client.sendall(msg)
    temp.sent += 1

server.start()
connect_clients(4000)

import matplotlib.pyplot as plt
def sample():
    x = []
    while threading.active_count() > 5:
        x.append(threading.active_count())
        plt.plot(x)
        # plt.axis([0, 6, 0, 20])
        plt.show()
