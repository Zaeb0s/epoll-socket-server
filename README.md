# ESocketS
ESocketS is a python 3 socket.socket server. There are many socket.socket python modules out there, I choose to write this because I failed to find one that met my requirements and at the same time was easy enough to understand. ESocketS uses non-blocking sockets with select.epoll() to check for read/write/error socket changes.

## When to use ESocketS?
EsocketS is written for one purpose above all, servers that need to support a high client count. An ESocketS server client count is restricted by the amount of file descriptors availible on the system.

## Important notes about changes
* 2015-12-15: Changed the name of some of the "on" functions.
* 2015-12-17: Several choices added when calling ESocketS.Socket()
* 2015-12-22: Large update, I expect most programs previously built on this module will not work as is anymore

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
* Socket: The Socket server class

The "on" functions are called by the ESocketS.Socket class at each specific event in a new thread. The functions does not need to be specified in the subclass. However I recommend not playing around with the other built in functions.

```python
#!/bin/env python3
import ESocketS

class Sock(ESocketS.Socket):
    def on_start(self):
        print('Server started on: ', self.host, self.port)

    def on_connect(self, conn):
        print(self.get_ip(conn), 'Connected')

    def on_recv(self, conn, data):
        print(self.get_ip(conn), ': ', data)
        for i in self.get_clients():
            i.send(data)

    def on_disconnect(self, conn):
        print(self.get_ip(conn), 'Disconnected')

    def on_abnormal_disconnect(self, conn, msg):
        print('Abnormal disconnect: ', msg)

    def on_stop(self):
        print('Server closed')

    def on_warning(self, msg):
        print('Warning: ', msg)

s = Sock()
s.start()
```

The above example shows the simplest way to start a server. For the more advanced user there are several initiation options available. The following shows all available parameters and their default values.

```python
s = Socket(port=1234,
           host=socket.gethostbyname(socket.gethostname()),
           queue_size=1000,
           epoll_block_time=2)
```

* port - The server port
* host - The sever host name
* queue_size - The maximum number of clients awaiting to be accepted by the server socket
* epoll_block_time - Each selector block will block at max this time in seconds

To send a message to a client do

```python
s.send(conn, b'Hello from server')
```

Where "conn" is the client socket object passed to most of the "on" functions. Messages can be sent to the same client from multiple threads at the same time without getting scrambled. (Only one thread per user that calls the conn.send function is active at one time) if one thread is currently flushing the send buffer queue.Queue object a call to s.send will only put the message into the queue.Queue object. The thread sending data dies when the queue is empty.

The "on" functions can be setup so that the server calls them within a new subthread. For instance if we wanted to run the on_recv within a subthread on each call do

```python
s.run_in_subthread(s.on_recv, True)
```
## Receiving messages
Although there is a built in function to receive messages that calls the on_recv function, users are encurraged to write a custom recv function to handle incomming messages
The built in function looks like this

```python
def recv(self, conn):
    try:
        data = conn.recv(self.default_recv_buffsize)
    except socket.error:
        self.disconnect(conn, False, 
                        'Error while receiving data from {}'.format(self.get_ip(conn)))
    else:
        if data == b'':
            self.disconnect(conn)
        else:
            self.register(conn)
            self._call_on_function(self.on_recv, (conn, data))
```
Whithin the recv function users are expected to take data from the recv buffer using the socket objects conn.recv(bytes) function. If more data is expected from the client in question when done receiving call the self.register(conn) function to continue listening for incoming messages.

## Disconnecting

```python
def disconnect(self, conn, normal=True, msg=''):
    if self._client_info[conn].is_registered:
        self.unregister(conn)
    try:
        conn.shutdown(socket.SHUT_RDWR)
    except socket.error:
        pass
    conn.close()
    if normal:
        self._call_on_function(self.on_disconnect, (conn, ))
    else:
        self._call_on_function(self.on_abnormal_disconnect, (conn, msg))
    del self._client_info[conn]

```


## Planned releases
- EWebsocketS - A Websocket server based on ESocketS and the RFC6455 websocket protocol

## Contact
Find something hard to understand? Do you have any suggestions of further improvement? If so do not hesitate to contact me on christoffer_zakrisson@hotmail.com
