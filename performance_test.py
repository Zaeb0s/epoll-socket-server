#!/bin/env python3
import socket
import threading
from time import sleep
host = socket.gethostbyname(socket.gethostname())
port = 1234

def connect(clients):
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((host, port))
    clients.append(conn)
    
clients = []
for i in range(2000):
    threading.Thread(target=connect, args=(clients,)).start()
    sleep(0.01)


