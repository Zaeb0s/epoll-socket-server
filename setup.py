#!/bin/env python3
from distutils.core import setup
setup(
  name = 'EScocketS',
  packages = ['ESocketS'], # this must be the same as the name above
  version = '0.1',
  description = 'A socket server using select.epoll',
  author = 'Christoffer Zakrisson',
  author_email = 'christoffer_zakrisson@hotmail.com',
  url = 'https://github.com/peterldowns/mypackage', # use the URL to the github repo
  download_url = 'https://github.com/Zaeb0s/epoll-socket-server/tarball/0.1', # I'll explain this in a second
  keywords = ['socket', 'epoll', 'server', 'poll', 'select', 'TCP', 'web'], # arbitrary keywords
  classifiers = [],
)
