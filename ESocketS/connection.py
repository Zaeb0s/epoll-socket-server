#!/bin/env python3

class Connection:
    def __init__(self, conn, address):
        self.conn = conn
        self.address = address

        self.recv_buffer = []
        self.send_buffer = []

        self.flushing_send_buffer = False

        self.conn.setblocking(0)

    def fileno(self):
        return self.conn.fileno()

    def close(self):
        return self.conn.close()

    def send(self, data):
        self.send_buffer.append(data)
        if not self.flushing_send_buffer:
            self.flushing_send_buffer = True
            while len(self.send_buffer) != 0:
                frame = self.send_buffer.pop(0)
                total_sent = 0
                to_send = len(frame)
                while total_sent < to_send:
                    sent = self.conn.send(frame[total_sent:])
                    if sent == 0:
                        raise SendError('Could not send some or all of a frame to: %s' % self.getip())
                    else:
                        total_sent += sent
            else:
                self.flushing_send_buffer = False

    def getip(self):
        return '%s:%s' % self.address

class SendError(Exception):
    pass
    

