#!/bin/env python3

def bytes2int(data):
    """ Converts bytes list/string to unsigned decimal """
    return int.from_bytes(data, byteorder='big')


def int2bytes(data, size):
    return data.to_bytes(size, byteorder='big')

