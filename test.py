#!/bin/env python3
import ESocketS

class Sock(ESocketS.Socket):
    def on_start(self):
        print('Server started on: ', self.host, self.port)

    def on_connect(self, conn):
        print(self.get_ip(conn), 'Connected')

    def on_recv(self, conn, data):
        print(self.get_ip(conn), ': ', data)
        for i in self.get_clients():
            i.send(data)

    def on_disconnect(self, conn):
        print(self.get_ip(conn), 'Disconnected')

    def on_abnormal_disconnect(self, conn, msg):
        print('Abnormal disconnect: ', msg)

    def on_stop(self):
        print('Server closed')

    def on_warning(self, msg):
        print('Warning: ', msg)

s = Sock()
s.start()


