# ESocketS
ESocketS is a python 3 socket.socket server. There are many socket.socket python modules out there, I choose to write this because I failed to find one that met my requirements and at the same time was easy enough to understand. ESocketS uses non-blocking sockets with select.epoll() to check for read/write/error socket changes.

## When to use ESocketS?
EsocketS is written for one purpose above all, servers that need to support a high client count. An ESocketS server client count is restricted by the amount of file descriptors availible on the system.

## Important notes about changes
* 2015-12-15: Changed the name of some of the "on" functions.
* 2015-12-17: Several choices added when calling ESocketS.Socket()

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

The "on" functions are called by the ESocketS.Socket class at each specific event in a new thread. The functions does not need to be specified in the subclass. However I recommend not playing around with the other built in functions.
```python
#!/bin/env python3
import ESocketS


class Sock(ESocketS.Socket):
    def on_start(self):
        print('Server started on: ', self.host, self.port)

    def on_connect(self, fileno):
        print(self.clients[fileno].getip(), 'Connected')

    def on_recv(self, fileno, msg):
        print(msg)

    def on_disconnect(self, fileno):
        print(self.clients[fileno].getip(), 'Disconnected')
        del self.clients[fileno]

    def on_abnormal_disconnect(self, fileno, msg):
        print('Abnormal disconnect: ', msg)
        del self.clients[fileno]

    def on_server_shutting_down(self):
        print('Server shutting down')

    def on_server_shut_down(self):
        print('Server is now closed')

    def on_warning(self, msg):
        print('Warning: ', msg)


s = Sock()
s.start()

```

The above example shows the simplest way to start a server. For the more advanced user there are several initiation options available. The following shows all available parameters and their default values.
```python
s = Socket(  port=1234,
             host=socket.gethostbyname(socket.gethostname()),
             BUFFER_SIZE=2048,
             QUEUE_SIZE=100,
             SERVER_EPOLL_BLOCK_TIME=10,
             CLIENT_EPOLL_BLOCK_TIME=1,
             clients_class=connection.Connection,
             queue_recv_messages=False,
             auto_register = True
             run_on_in_subthread=True)
```
* port - The server port
* host - The serun_on_in_subthread: Specifies whether or not to run the "on" functions in subthreads using
        threading.Threadrun_on_in_subthread: Specifies whether or not to run the "on" functions in subthreads using
        threading.Threadrver host name
* BUFFER_SIZE - The maximum size that the server will receive data at one time from a client
* QUEUE_SIZE - The maximum number of clients awaiting to be accepted by the server socket
* SERVER_EPOLL_BLOCK_TIME - Each epoll() in the server thread call will block at max this time in seconds
* CLIENT_EPOLL_BLOCK_TIME - Each epoll() in the client thread call will block at max this time in seconds
* queue_recv_messages - Tells whether or not to save the messages received from clients in the s.clients[fileno].recv_queue queue.Queue object
* client_class - This lets a user setup a subclass of the connection.Connection (replace this with the connection.Connection subclass)
* auto_register - When the server detects new incoming data it unregisters the client in question from the epoll object while reading the socket. True - Automatically register when server is done receiving from client False - When the user is ready to receive new messages from client the user must again register the client to the client_epoll object using self.register(fileno)
* run_on_in_subthread - Specifies whether or not to run the "on" functions in subthreads using threading.Thread

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
