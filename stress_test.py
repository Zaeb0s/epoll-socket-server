#!/bin/env python3

import socket
import threading
from random import random
from time import sleep
# host = '192.168.1.5'
# host = '130.240.202.41'

no_clients = 20
messages_per_second = 0.0000001
message = b'hello server'

# def send_messages():
#
#     i = 0
#     print('Sending messages at {} m/s'.format(messages_per_second))
#     ms = messages_per_second
#     while True:
#         if ms != messages_per_second:
#             ms = messages_per_second
#             print('Sending messages at {} m/s'.format(messages_per_second))
#
#         t1 = time()
#         i_client = i % len(clients)
#         ping1 = time()
#         clients[i_client].send(message)
#         clients[i_client].recv(len(message))
#         ping = (time() - ping1)*1000
#         if (i % 100) == 0:
#             print('Ping: ' + str(ping))
#         i += 1
#         t2 = time()
#         sleep(max(0, 1/messages_per_second - (t2-t1)))


host = '192.168.1.7'
# host = '213.113.6.13'
ports = range(8000, 8100)


def connect(host, port):
    # sleep(random()/100)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.connect((host, port))
    sock.recv(1)
    return sock


clients = []
i = 0
def users(no_users, port):
    if no_users > len(clients):
        no_to_connect = no_users - len(clients)
        for i in range(no_to_connect):
            # port = ports[i % len(ports)]
            clients.append(connect(host, port))
            print('Connected: {}:{}'.format(host,port))
    elif no_users < len(clients):
        no_to_close = len(clients) - no_users
        for i in range(no_to_close):
            client = clients.pop()
            client.shutdown(socket.SHUT_RDWR)
            client.close()
    print('User count now: {}'.format(len(clients)))


# threading.Thread(target=send_messages).start()

for port in ports:
    threading.Thread(target=users, args=(5000, port)).start()



