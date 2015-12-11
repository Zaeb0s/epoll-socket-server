#!/bin/env python3
from bytes_convert import int2bytes
import socket


class Action:
    CONTINUE        = b'0'
    ADD_CLIENT      = b'1'
    REMOVE_CLIENT   = b'2'

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.sock.connect((self.host, self.port))

    def send(self, action, fileno=None, nobytes=2):
        if fileno:
            try:
                fn = int2bytes(fileno, nobytes)
            except OverflowError:
                return self.send(action, fileno, nobytes+1)

            frame = action+fn

            return self.sock.send(int2bytes(len(frame), 1) + action + fn)
        else:
            return self.sock.send(b'\x01' + action)

