# esockets
esockets is a python socket.socket server. There are many socket.socket python modules out there, I choose to write this because I failed to find one that met my requirements and at the same time was easy enough to understand. esockets uses non-blocking sockets with select.epoll() to check for read/write/error socket changes.

## When to use esockets?
esockets is written for one purpose above all, servers that need to support a high client count. An esockets server client count is restricted by the amount of file descriptors availible on the system.

## Important notes about changes
* 2015-12-15: Changed the name of some of the "on" functions.
* 2015-12-17: Several choices added when calling ESocketS.Socket()
* 2015-12-22: Large update, I expect most programs previously built on this module will not work as is anymore
* 2016-02-14: Updated the readme file

## How to get started
### Installation
```sh
pip install esockets
```
### Update
At the moment (2016-02-14) this module is still new. As I try to integrate it into my other projects I usually find something to improve. So to get the latest version do
```sh
pip install esockets --upgrade
```
See <https://github.com/Zaeb0s/epoll-socket-server> for the latest changes
### Basic setup
The user communicates with the ServerSocket class using two functions (handle_incoming and handle_readable) that returns True/False.

The following is a simple example of an echo server

```python
#!/bin/env python3
import esockets
def handle_incoming(client, address):
    """
    Return True: The client is accepted and the server starts polling for messages
    Return False: The server disconnects the client.
    """
    
    client.sendall(b'SERVER: Connection accepted!\n')
    return True

def handle_readable(client):
    """
    Return True: The client is re-registered to the selector object.
    Return False: The server disconnects the client.
    """
    
    data = client.recv(1028)
    if data == b'':
        return False
    client.sendall(b'SERVER: ' + data)
    return True

server = esockets.SocketServer(handle_incoming=handle_incoming,
                               handle_readable=handle_readable)
server.start()
print('Server started on: {}:{}'.format(server.host, server.port))
```

### Customizable variables

When the SocketServer is initiated the following customizable variables are set if not otherwise specified

Variable | Description | Default
---------|-------------|--------
port | The server port | 1234
host | The server host |  Using the socket modules socket.gethostbyname(socket.gethostname())
queue_size | Max number of clients awaiting to be accepted | 1000
block_time | Maximum block time within each selector and queue objects | 2
selector | A selectors object to determine which type to use | selectors.EpollSelector
max_subthreads | Maximum number of threads started in addition to the four mainthreads | -1 (Unlimited)
Calling with all default values would then look like this

```python
server = esockets.SocketServer(  port=1234,
                                 host=socket.gethostbyname(socket.gethostname()),
                                 queue_size=1000,
                                 block_time=2,
                                 selector=selectors.EpollSelector,
                                 handle_readable=lambda client: True,
                                 handle_incoming=lambda client, address: True,
                                 max_subthreads=-1):
```


## Planned releases
- ewebsockets - A Websocket server based on esockets and the RFC6455 websocket protocol

## Contact
Find something hard to understand? Do you have any suggestions of further improvement? If so do not hesitate to contact me on christoffer_zakrisson@hotmail.com
