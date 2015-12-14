# ESocketS
ESocketS is a python 3 socket.socket server. There are many socket.socket python modules out there, I choose to write this because I failed to find one that met my requirements and at the same time was easy enough to understand. ESocketS uses non-blocking sockets with select.epoll() to check for read/write/error socket changes.

## When to use ESocketS?
EsocketS is written for one purpose above all, servers that need to support a high client count. An ESocketS server client count is restricted by the amound of file descriptors availible on the system.

## How to get started
### Installation
```sh
pip install ESocketS
```
### Update
At the moment (2015-12-14) this module is still new. As I try to integrate it into my other projects I usually find something to improve. So to get the latest version do
```sh
pip install ESocketS --upgrade
```
See <https://github.com/Zaeb0s/epoll-socket-server> for the latest changes
### Integration
ESocketS consists of two main classes, the Socket and Connection classes.
- Socket: The Socket server class
- Connection: Can be considered as a subclass of the client socket object 

The "on" functions are called by the ESocketS.Socket class at each specific event in a new thread. The functions does not need to be specified in the subclass. However I recommend not playing arround with the other bult in functions.
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
        del self.clients[fileno]
        
    def on_server_shutting_down(self):
        print('Server shutdown sequence started')

    def on_server_shut_down(self):
        print('Server closed')

    def on_warning(self, msg):
        print('Warning: ', msg)
        
s = Socket(port=1234)
s.start()
```

The above example shows the simplest way to start a server. For the more advanced user there are several initiation options availible. The following shows all availible parameters and their default values.
```python
s = Socket(  port=1234,  #  The server port
             host=socket.gethostbyname(socket.gethostname()),  # The server host name
             BUFFER_SIZE=2048,  # The maximum size that the server will receive data at one time from a client
             QUEUE_SIZE=100,  # The maximum number of clients awaiting to be accepted by the server socket
             SERVER_EPOLL_BLOCK_TIME=10,  # Each epoll() in the server thread call will block at max this time in seconds
             CLIENT_EPOLL_BLOCK_TIME=1,    # Each epoll() in the client thread call will block at max this time in seconds
             QUEUE_RECV_MESSAGES=False,  # Tells wether or not to save the messages received from clients in the s.clients[fileno].recv_queue queue.Queue object
             clients_class=connection.Connection)  # This lets a user setup a subclass of the connection.Connection (replace this with the connection.Connection subclass)
```
The client objects are stored in in a dictionary s.clients by their corresponding file number. NOTE: The client is not deleted from this dictionary on client disconnect, the client is only unregistered from the client epoll object.\

To send a message to a client do
```python
s.clients[fileno].send(b'Hello from server')
```
Messages can be sent to the same client from multiple threads at the same time without getting scrambled. (Only one thread per user that calls the socket.send function is active at one time) if one thread is currently flushing the s.clients[fileno].send_buffer queue.Queue object a call to s.clients[fileno].send(message) will only put the message into the queue.Queue object

## Planned releases
- EWebsocketS - A Websocket server based on ESocketS and the RFC6455 websocket protocol

## Contact
Find something hard to understand? Do you have any suggestions of further improvement? If so do not hesitate to contact me on christoffer_zakrisson@hotmail.com


