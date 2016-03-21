#!/bin/env python3
import esockets
import logging, sys
import socket
root = logging.getLogger()
root.setLevel(logging.ERROR)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)
#
class MyClientHandler(esockets.ClientHandler):
    def handle_socket_message(self):
        message = self.recv(1024).strip()
        print(self.address(), message)
        # print('Client: ', message)
        self.send(b'Server: ' + message + b'\n')
        return True

    def handle_socket_accept(self):
        # print(self.address, ' Connected')
        self.send(b'1')
        return True

    def handle_socket_close(self, reason=''):
        pass
        # self.send(b'Closing socket: ' + reason.encode() + b'\n')
        # print(self.address, ' Disconnected: ', reason)


try:
    host = sys.argv[1]
except IndexError:
    # host = '192.168.56.1'
    host = socket.gethostbyname(socket.gethostname())

try:
    port = int(sys.argv[2])
except IndexError:
    port = range(8000, 9000)

# host = '130.240.202.41'
server = esockets.SocketServer(host=host, port=port, client_handler=MyClientHandler,
                               queue_size=1000)
#
server.start()
# print('Server started on: {}:{}'.format(server.host, server.port))
#
# # server = esockets.SocketServer()
# # server.start()

# import socketserver
#
#
# clients = []
#
# class Client(socketserver.BaseRequestHandler):
#     def handle(self):
#         print(self.client_address, ' Connected')
#         clients.append(self.request)
#         return True
#
# HOST, PORT = "localhost", 9999
#
# # Create the server, binding to localhost on port 9999
# server = socketserver.TCPServer((HOST, PORT), Client)
# server.allow_reuse_address  = True
# server.serve_forever(2)

