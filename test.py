#!/bin/env python3
from ESocketS.socket_server import Socket
from threading import Thread
class Sock(Socket):
    def on_start(self):
        print('Server started on: ', self.host, self.port)

    def on_connect(self, conn):
        print(self.get_ip(conn), 'Connected')
        self.register(conn)

    def on_recv(self, conn, data):
        self.register(conn)
        print(self.get_ip(conn), ': ', data)
        for i in self.get_clients():
            Thread(target=self.send_raw, args=(i, data)).start()


    def on_disconnect(self, conn):
        print(self.get_ip(conn), 'Disconnected')

    def on_abnormal_disconnect(self, conn, msg):
        print('Abnormal disconnect: ', msg)

    def on_stop(self, msg):
        print('Server closed: ', msg)

    def on_warning(self, msg):
        print('Warning: ', msg)



s = Sock()
s.start()