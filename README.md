# ESocketS
ESocketS is a python 3 socket.socket server. There are many socket.socket python modules out there, I choose to write this because I failed to find one that met my requirements and at the same time was easy enough to understand. ESocketS uses non-blocking sockets with select.epoll() to check for read/write/error socket changes.

## When to use ESocketS?
EsocketS is written for one purpose above all, servers that need to support a high client count. An ESocketS server client count is restricted by the amound of file descriptors availible on the system.

## How to get started
### Installation
```sh
pip install ESocketS
```

### Integration
ESocketS consists of two main classes, the Socket and Connection classes.
- Socket: The Socket server class
- Connection: Can be considered as a subclass of the client socket object 

The "on" functions are called by the ESocketS.Socket class at each specific event in a new thread. The functions does not need to be specified in the subclass. However I recommend not playing around with the other bult in functions.
```python
#!/bin/env python3
import ESocketS
class Socket(ESocketS.Socket):
    def on_client_connect(self, fileno):
        print(self.clients[fileno].getip(), 'Connected')

    def on_start(self):
        print('Server started on: ', self.host, self.port)

    def on_message_recv(self, fileno, msg):
        print(self.clients[fileno].getip(), ': ', msg)

    def on_client_disconnect(self, fileno):
        print(self.clients[fileno].getip(), 'Disconnected')

    def on_server_shutting_down(self):
        print('Server shutdown sequence started')

    def on_server_shut_down(self):
        print('Server closed')

    def on_warning(self, msg):
        print('Warning: ', msg)
        
s = Socket(port=1234)
s.start()
```
The client objects are stored in in a dictionary s.clients by their corresponding file number.

## Contact
Find something hard to understand? Do you have any suggestions of further improvement? If so do not hesitate to contact me on christoffer_zakrisson@hotmail.com


