#!/bin/env python3
import ESocketS
import socket

class Sock(ESocketS.Socket):

    def on_start(self):
        print('Server started on: ', self.host, self.port)

    def on_connect(self, fileno):
        print(self.clients[fileno].getip(), 'Connected')

    def on_recv(self, fileno, msg):
        print(msg)

    def on_disconnect(self, fileno):
        print(self.clients[fileno].getip(), 'Disconnected')

    def on_abnormal_disconnect(self, fileno, msg):
        print('Abnormal disconnect: ', msg)
        
    def on_server_shutting_down(self):
        print('Server shutting down')

    def on_server_shut_down(self):
        print('Server is now closed')

    def on_warning(self, msg):
        print('Warning: ', msg)


s = Sock()
s.start()

    
    
    
    
    
    
    
