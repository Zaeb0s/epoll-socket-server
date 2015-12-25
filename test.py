#!/bin/env python3
import ESocketS
from threading import Thread


class Sock(ESocketS.Socket):
    def on_start(self):
        print('Server started on: ', self.host, self.port)

    def on_connect(self, conn):
        """Here you can:
         -  Change the recv function and arguments
            using self.clients[conn].callback_function and
            self.clients[conn].callback_args = (arg1, arg2, ...)
        -   register the client
            If you want to start polling for changes in the client socket use self.register(conn)
            This will register the client to the selector with the callback_function and
            callback_arguments the default is self.recv(conn)

        """
        print(self.get_ip(conn), 'Connected')
        self.register(conn)

    def on_poll(self, conn):
        try:
            data = self.recv(conn, 100)
        except(ESocketS.ClientDisconnect, ESocketS.ClientAbnormalDisconnect):
            print(self.clients[conn].address, 'Disconnected')
            self.disconnect(conn)
        except ESocketS.WouldBlock:
            self.register(conn)
        else:
            self.register(conn)
            print(self.clients[conn].address, ': ', data)
            for i in self.get_clients():
                Thread(target=self.send, args=(i, data)).start()


    def on_abnormal_disconnect(self, conn, msg):
        print('Abnormal disconnect: ', msg)

    def on_stop(self, msg):
        print('Server closed: ', msg)

    def on_warning(self, msg):
        print('Warning: ', msg)



s = Sock()
s.start()
