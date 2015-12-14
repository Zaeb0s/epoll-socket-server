#!/bin/env python3
import queue

class Connection:
    def __init__(self, conn, address, recv_queue=False):
        self.conn = conn
        self.address = address

        if recv_queue:
            self.recv_buffer = queue.Queue()
        else:
            self.recv_buffer = None

        self.send_buffer = queue.Queue()

        self.flushing_send_buffer = False

        self.conn.setblocking(0)

    def fileno(self):
        return self.conn.fileno()

    def close(self):
        return self.conn.close()

    def shutdown(self, type):
        return self.conn.shutdown(type)

    def send(self, msg):
        if type(msg) == str:
            msg = msg.encode()
        elif type(msg) == bytes:
            pass
        else:
            raise TypeError('The message should be either a string or bytes object')
        self.send_buffer.put(msg)

        if not self.flushing_send_buffer:
            self.flushing_send_buffer = True
            try:
                while True:
                    data = self.send_buffer.get(block=False)
                    to_send = len(data)
                    total_sent = 0
                    while total_sent < to_send:
                        sent = self.conn.send(data[total_sent:])
                        if sent == 0:
                            raise Broken('Could not send some or all of a frame to: %s' % self.getip())
                        else:
                            total_sent += sent
            except queue.Empty:
                self.flushing_send_buffer = False

    def recv(self, size):
        data = self.conn.recv(size)
        if data == b'':
            raise Broken('Connection closed by client')
        else:
            if self.recv_buffer:
                self.recv_buffer.put(data)
            return data

    def getip(self):
        return '%s:%s' % self.address


class Broken(Exception):
    pass
