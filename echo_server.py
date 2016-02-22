#!/bin/env python3
import esockets
import logging, sys

root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

def handle_incoming(client, address):
    """
    Return True: The client is accepted and the server starts polling for messages
    Return False: The server disconnects the client.
    """

    client.sendall(b'SERVER: Connection accepted!\n')
    return True

def handle_readable(client):
    """
    Return True: The client is re-registered to the selector object.
    Return False: The server disconnects the client.
    """

    data = client.recv(1028)
    if data == b'':
        return False
    client.sendall(b'SERVER: ' + data)
    return True

server = esockets.SocketServer(handle_incoming=handle_incoming,
                               handle_readable=handle_readable)
server.start()
print('Server started on: {}:{}'.format(server.host, server.port))

# server = esockets.SocketServer()
# server.start()