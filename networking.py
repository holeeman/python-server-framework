# coding=UTF-8

'''
Networking Module
by Hosung Lee (runway3207@hanmail.net)
'''

import threading
import thread
import socket
import Queue
import json
import struct

NET_SOCKET_CREATED = 100
NET_SOCKET_CLOSED = 500
NET_CLIENT_CONNECTED = 110
NET_CLIENT_DISCONNECTED = 510
NET_CONNECTION_ACCEPTED = 111
NET_CONNECTION_ESTABLISHED = 112
NET_CONNECTION_CLOSED = 511
NET_HEADER = 137


class Message(object):
    def __init__(self, encoded_data=None):
        self.dest_socket = None
        self.data = {}
        if encoded_data:
            self.data = json.loads(encoded_data)

    def read(self, key):
        try:
            return self.data[key]
        except KeyError:
            return None

    def write(self, key, value):
        self.data.update({key: value})

    def get_packet(self):
        data = struct.pack("B", NET_HEADER) + json.dumps(self.data)
        return struct.pack("H", len(data)) + data

    def __repr__(self):
        return str(self.data)


class Client(object):
    def __init__(self, socket_id, soc, ip_address):
        self.socket_id, self.socket, self.ip_address = socket_id, soc, ip_address
        self.status = NET_CLIENT_CONNECTED

    def disconnect(self):
        # disconnect client from server
        self.socket.close()
        self.status = NET_CLIENT_DISCONNECTED


class NetworkingSocket(threading.Thread):
    thread_id_assigner = 0

    def __init__(self, host, port, protocol=None):
        threading.Thread.__init__(self)

        self.socket_id_list = []
        self.socket_id_assigner = 0

        self.host, self.port, self.protocol = host, port, protocol
        self.size = 1024
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.status = NET_SOCKET_CREATED
        self.threadID = self.__class__.thread_id_assigner
        self.socket_id = -1
        self.__class__.thread_id_assigner += 1
        self.sending_queue_lock = threading.Lock()
        self.receiving_queue_lock = threading.Lock()
        self.list_lock = threading.Lock()
        self.sending_queue = Queue.Queue()
        self.receiving_queue = Queue.Queue()

    def disconnect(self, soc):
        pass

    def close(self):
        # wait until sending queue is empty
        while not self.sending_queue.empty():
            pass
        self.socket.close()
        self.status = NET_SOCKET_CLOSED

    def get_status(self):
        # get status of current socket
        return self.status

    def sender(self):
        # message sender thread
        while self.status != NET_SOCKET_CLOSED:
            self.sending_queue_lock.acquire()
            if not self.sending_queue.empty():
                message = self.sending_queue.get()
                message.write("sender", self.socket_id)
                try:
                    message.dest_socket.sendall(message.get_packet())
                except socket.error:
                    self.disconnect(message.dest_socket)
            self.sending_queue_lock.release()

    def receiver(self, soc):
        # message receiver thread
        while self.status != NET_SOCKET_CLOSED and soc:
            try:
                data = soc.recv(struct.calcsize("H"))
            except socket.error:
                self.disconnect(soc)
                break
            if not data or len(str(data)) < 2:
                continue

            packet_size = struct.unpack("H", data)[0]
            received_data = ""

            while len(received_data) < packet_size:
                # on first loop, check for header
                if received_data == "":
                    data = soc.recv(struct.calcsize('B'))
                    if struct.unpack("B", data)[0] != NET_HEADER:
                        received_data = None
                        break
                else:
                    data = soc.recv(packet_size - len(received_data))

                # if no data is received, disconnect client from server
                if not data:
                    self.disconnect(soc)
                    received_data = None
                    break
                received_data += data

            if not received_data:
                continue

            # remove header
            received_data = received_data[1:len(received_data)]

            message = Message(received_data)
            if message.read("flag") == NET_CONNECTION_CLOSED:
                self.disconnect(soc)
                continue
            self.receiving_queue_lock.acquire()
            self.receiving_queue.put(message)
            self.receiving_queue_lock.release()

    def get_socket(self):
        return self.socket

    def get_message(self):
        # get message from message queue
        self.receiving_queue_lock.acquire()
        _data = self.receiving_queue.get()
        self.receiving_queue_lock.release()
        return _data

    def message_empty(self):
        # returns True if message queue is empty
        self.receiving_queue_lock.acquire()
        _empty = self.receiving_queue.empty()
        self.receiving_queue_lock.release()
        return _empty

    def bind_socket_id(self):
        if not len(self.socket_id_list):
            socket_id = self.socket_id_assigner
            self.socket_id_assigner += 1
        else:
            socket_id = self.socket_id_list[0]
            del self.socket_id_list[0]
        return socket_id

    def unbind_socket_id(self, socket_id):
        if socket_id >= 0:
            self.socket_id_list.append(socket_id)
            self.socket_id_list.sort()

    def send(self, soc, message):
        # send message to given socket
        message.dest_socket = soc
        self.sending_queue_lock.acquire()
        self.sending_queue.put(message)
        self.sending_queue_lock.release()


class ServerSocket(NetworkingSocket):
    def run(self):
        # set server's socket_id
        self.socket_id = self.bind_socket_id()

        # starting sender thread
        thread.start_new_thread(self.sender, ())

        while self.status != NET_SOCKET_CLOSED:
            # accepting new client
            new_socket, new_ip = self.socket.accept()
            new_id = self.bind_socket_id()
            new_client = Client(new_id, new_socket, new_ip)
            self.list_lock.acquire()
            self.client_list.update({new_id: new_client})
            self.list_lock.release()
            try:
                # start receiver thread
                thread.start_new_thread(self.receiver, (new_socket,))
            except thread.error, e:
                print e

            # send new_id to new client
            new_message = Message()
            new_message.write("flag", NET_CONNECTION_ACCEPTED)
            new_message.write("socket_id", new_id)
            self.send(new_socket, new_message)

    def bind(self):
        # bind server socket
        try:
            self.socket.bind((self.host, self.port))
        except socket.error, e:
            print e
            self.socket.close()
        self.client_list = {}

        self.socket.listen(5)

    def close(self):
        # send all client message
        for client in self.get_client_list():
            new_message = Message()
            new_message.write("flag", NET_CONNECTION_CLOSED)
            self.send(client.socket, new_message)

        # wait until sending queue is empty
        while not self.sending_queue.empty():
            pass
        self.socket.close()
        self.status = NET_SOCKET_CLOSED

    def disconnect(self, soc):
        for client in self.get_client_list():
            if client.socket == soc:
                if client.status == NET_CLIENT_DISCONNECTED:
                    break

                # disconnect client from server
                self.unbind_socket_id(client.socket_id)
                client.disconnect()
                self.list_lock.acquire()
                del self.client_list[client.socket_id]
                self.list_lock.release()

                # message to myself for notification
                new_message = Message()
                new_message.write("sender", client.socket_id)
                new_message.write("flag", NET_CONNECTION_CLOSED)
                self.receiving_queue_lock.acquire()
                self.receiving_queue.put(new_message)
                self.receiving_queue_lock.release()
                break

    def get_client(self, client_id):
        # get client object with given id
        self.list_lock.acquire()
        try:
            _client = self.client_list[client_id]
        except KeyError:
            _client = None
        self.list_lock.release()
        return _client

    def get_client_socket(self, client_id):
        # get client socket with given id
        _client = self.get_client(client_id)
        if _client:
            return _client.socket

    def get_client_list(self):
        # get client list of current server
        self.list_lock.acquire()
        _list =  self.client_list.values()
        self.list_lock.release()
        return _list


class ClientSocket(NetworkingSocket):
    def start(self):
        # starting sender thread
        thread.start_new_thread(self.sender, ())
        thread.start_new_thread(self.receiver, (self.socket, ))

        # wait until server responds
        while self.message_empty():
            pass

        message = self.get_message()
        if message.read("flag") == NET_CONNECTION_ACCEPTED:
            # get socket_id
            self.socket_id = message.read("socket_id")

            # send message to server
            new_message = Message()
            new_message.write("flag", NET_CONNECTION_ESTABLISHED)
            self.send(self.socket, new_message)

            # send message to myself
            new_message = Message()
            new_message.write("flag", NET_CONNECTION_ESTABLISHED)
            self.receiving_queue_lock.acquire()
            self.receiving_queue.put(new_message)
            self.receiving_queue_lock.release()

        return self.socket_id

    def connect(self):
        # connect to server
        self.socket.connect((self.host, self.port))

    def disconnect(self, soc):
        # message to myself for notification
        new_message = Message()
        new_message.write("sender", 0)
        new_message.write("flag", NET_CONNECTION_CLOSED)

        self.receiving_queue_lock.acquire()
        self.receiving_queue.put(new_message)
        self.receiving_queue_lock.release()

    def close(self):
        # disconnect from server

        while not self.sending_queue.empty():
            pass
        self.socket.close()
        self.status = NET_SOCKET_CLOSED


def connect(host, port):
    client = ClientSocket(host, port)
    client.connect()
    client.start()
    return client


def create_server(host, port):
    server = ServerSocket(host, port)
    server.bind()
    server.start()
    return server


def destroy(networking_socket):
    networking_socket.close()


def get_message(networking_socket):
    return networking_socket.get_message()


def message_available(networking_socket):
    return not networking_socket.message_empty()
