#!/bin/env python3
from distutils.core import setup
setup(
  name = 'ESocketS',
  packages = ['ESocketS'], # this must be the same as the name above
  version = '0.1.8',
  description = 'A socket server using select.epoll',
  author = 'Christoffer Zakrisson',
  author_email = 'christoffer_zakrisson@hotmail.com',
  url = 'https://github.com/Zaeb0s/epoll-socket-server', # use the URL to the github repo
  keywords = ['socket', 'epoll', 'server', 'poll', 'select', 'TCP', 'web'], # arbitrary keywords
  classifiers = [],
)
