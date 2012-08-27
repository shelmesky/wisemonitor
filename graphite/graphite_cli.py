import pickle
from socket import socket
import struct
import time


class GraphiteClient(object):

    def __init__(self, carbon_server, text_port=2003, pickle_port=2004):
        self.carbon_server = carbon_server
        self.text_port = text_port
        self.pickle_port = pickle_port

    def send_text(self, path, value, timestamp=None):
        if timestamp is None:
            timestamp = int(time.time())  # now

        message = '{0} {1} {2}\n'.format(path, value, timestamp)
        self._send(self.text_port, message)

    def send_pickle(self, data):
        payload = pickle.dumps(data)
        header = struct.pack('!L', len(payload))
        message = header + payload
        self._send(self.pickle_port, message)

    def _send(self, port, message):
        sock = socket()
        sock.connect((self.carbon_server, port))
        sock.sendall(message)
