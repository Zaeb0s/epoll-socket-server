#!/bin/env python3

from setuptools import setup
from esockets import __version__
import sys


def readme():
    with open('README.rst') as f:
        return f.read()

print('Current version: ', __version__)
version = __version__.split('.')


if sys.argv[-1] == 'minor':
    version[2] = str(int(version[2]) + 1)
    del sys.argv[-1]
elif sys.argv[-1] == 'major':
    version[1] = str(int(version[1]) + 1)
    version[2] = '0'
    del sys.argv[-1]
elif sys.argv[-1] == 'huge':
    version[0] = str(int(version[0]) + 1)
    version[1] = '0'
    version[2] = '0'
    del sys.argv[-1]


version = '.'.join(version)
with open('esockets/version', 'w') as f:
    f.write(version)

setup(
    name='esockets',
    packages=['esockets'], # this must be the same as the name above
    version=version,
    include_package_data=True,
    license='MIT',
    description='A socket server',
    long_description=readme(),
    author='Christoffer Zakrisson',
    author_email='christoffer_zakrisson@hotmail.com',
    url='https://github.com/Zaeb0s/epoll-socket-server', # use the URL to the github repo
    keywords=['socket', 'epoll', 'server', 'poll', 'select', 'TCP', 'web', 'esockets'], # arbitrary keywords
    classifiers=['Development Status :: 4 - Beta',
                   'Programming Language :: Python :: 3.5',
                   'Operating System :: POSIX :: Linux',
                   'License :: OSI Approved :: MIT License'],
    install_requires=['loopfunction', 'maxthreads']
)

print('Installed version: ' + version)
