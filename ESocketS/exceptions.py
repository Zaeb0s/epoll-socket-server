#!/bin/env python3


class ClientDisconnect(Exception):
    pass


class ClientAbnormalDisconnect(Exception):
    pass


class WouldBlock(Exception):
    pass