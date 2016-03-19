#!/bin/env python3
import esockets
import socket
# import logging, sys
from time import sleep, time
from random import random
import psutil
import sys
from matplotlib import pyplot
import threading
# root = logging.getLogger()
# root.setLevel(logging.DEBUG)
# ch = logging.StreamHandler(sys.stdout)
# ch.setLevel(logging.DEBUG)
# formatter = logging.Formatter('%(levelname)s - %(message)s')
# ch.setFormatter(formatter)
# root.addHandler(ch)

# pid = int(sys.argv[1])

host = '192.168.1.5'
port = 1234

no_clients = 200
messages_per_second = 100
message = b'hello server'




# Find the process
# process = None
# for i in psutil.process_iter():
#     if i.pid == pid:
#         process = i
#         break

# if process is None:
#     raise RuntimeError('Could not find process')


def connect(host, port):
    sleep(random()/1000)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.connect((host, port))
    return sock


clients = []
# memory = [process.memory_info().rss/1e6]
# client_count = [0]
for i in range(no_clients):
    try:
        clients.append(connect(host, port))
        # memory.append(process.memory_info().rss/1e6)
        # client_count.append(len(clients))
    except OSError:
        break

# pyplot.plot(client_count, memory)
# pyplot.ylabel('MB')
# pyplot.xlabel('Client count')
# pyplot.show()
print('Successfully connected {} clients'.format(len(clients)))


def send_messages():

    i = 0
    print('Sending messages at {} m/s'.format(messages_per_second))
    ms = messages_per_second
    while True:
        if ms != messages_per_second:
            ms = messages_per_second
            print('Sending messages at {} m/s'.format(messages_per_second))

        t1 = time()
        i_client = i % len(clients)
        clients[i_client].send(message)
        clients[i_client].recv(len(message))
        i += 1
        t2 = time()
        sleep(max(0, 1/messages_per_second - (t2-t1)))

def users(no_users):
    if no_users > len(clients):
        for i in range(no_users-len(clients)):
            clients.append(connect(host,port))
    elif no_users < len(clients):
        no_to_close = len(clients) - no_users
        for i in range(no_to_close):
            client = clients.pop()
            client.shutdown(socket.SHUT_RDWR)
            client.close()
    print('User count now: {}'.format(len(clients)))


threading.Thread(target=send_messages).start()

# except KeyboardInterrupt:
#     for client in clients:
#         client.shutdown(socket.SHUT_RDWR)
#         client.close()
#     sys.exit(0)



