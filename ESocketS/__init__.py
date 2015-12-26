#!/bin/env python3
from ESocketS.socket_server import *

with open(__path__[0] + '/version', 'r') as r:
    __version__ = r.read()
