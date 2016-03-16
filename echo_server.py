#!/bin/env python3
import esockets
import logging, sys
import threading
root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

def handle_incoming(client):
    """
    Return True: The client is accepted and the server starts polling for messages
    Return False: The server disconnects the client.
    """

    client.send(b'SERVER: Connection accepted!\n')


    return True

def handle_readable(client):
    """
    Return True: The client is re-registered to the selector object.
    Return False: The server disconnects the client.
    """

    data = client.recv(200, fixed=False)
    if b'close' in data:
        return 'Client requested close'
    # client.close()
    client.send(b'SERVER: ' + data + b'\n')
    return True

def handle_closed(client, reason):
    print('Client socket closed: ', reason)

server = esockets.SocketServer(handle_incoming=handle_incoming,
                               handle_readable=handle_readable,
                               handle_closed=handle_closed)
server.start()
print('Server started on: {}:{}'.format(server.host, server.port))

# server = esockets.SocketServer()
# server.start()