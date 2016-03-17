#!/bin/env python3
import esockets
import logging, sys
import threading
root = logging.getLogger()
root.setLevel(logging.DEBUG)
fh = logging.FileHandler('spam.log')
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(fh)

class Client(esockets.Client):
    def handle_message(self):
        message = self.recv(1024, fixed=False).strip()
        print('Client: ', message)
        self.send(b'Server: ' + message + b'\n')
        self.close('Invalid request')

    def handle_accept(self):
        print(self.address, ' Connected: ')

    def handle_closed(self, reason):
        print(self.address, ' Disconnected: ', reason)

# def handle_incoming(client):
#     """
#     Return True: The client is accepted and the server starts polling for messages
#     Return False: The server disconnects the client.
#     """
#
#     client.send(b'SERVER: Connection accepted!\n')
#
#
#     # return True
#
# def handle_readable(client):
#     """
#     Return True: The client is re-registered to the selector object.
#     Return False: The server disconnects the client.
#     """
#
#     data = client.recv(1, fixed=False)
#
#
#     # if b'close' in data:
#     #     return 'Client requested close'
#     # client.close()
#     client.send(b'SERVER: ' + data + b'\n')


def handle_closed(client, reason):
    print('Client socket closed: ', reason)

# server = esockets.SocketServer(handle_incoming=handle_incoming,
#                                handle_readable=handle_readable,
#                                handle_closed=handle_closed)
server = esockets.SocketServer(client_class=Client)

server.start()
print('Server started on: {}:{}'.format(server.host, server.port))

# server = esockets.SocketServer()
# server.start()