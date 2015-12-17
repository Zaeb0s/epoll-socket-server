#!/bin/env python3
from distutils.core import setup

setup(
  name = 'ESocketS',
  packages = ['ESocketS'], # this must be the same as the name above
  version = '0.2.0',
  license = 'MIT',
  description = 'A socket server using select.epoll',
  author = 'Christoffer Zakrisson',
  author_email = 'christoffer_zakrisson@hotmail.com',
  url = 'https://github.com/Zaeb0s/epoll-socket-server', # use the URL to the github repo
  keywords = ['socket', 'epoll', 'server', 'poll', 'select', 'TCP', 'web'], # arbitrary keywords
  classifiers = ['Development Status :: 4 - Beta',
                 'Programming Language :: Python :: 3.5',
                 'Operating System :: POSIX :: Linux',
                 'License :: OSI Approved :: MIT License'],
)
