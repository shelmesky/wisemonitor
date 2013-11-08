#!--encoding:utf-8--
import threading
from pika.adapters.tornado_connection import TornadoConnection
import pika


class NagiosReceiver(object):
    """
    Receive alert from Nagios.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """singleton model"""
        if not cls._instance:
            NagiosReceiver._lock.acquire()
            cls._instance = super(NagiosReceiver, cls).__new__(
                cls, *args, **kwargs)
            NagiosReceiver._lock.release()
        return cls._instance
    
    def __init__(self, mq_server, username, password, virtual_host,
                 frame_size=131072, callback=None):
        self.mq_server = mq_server
        self.username = username
        self.password = password
        self.virtual_host = virtual_host
        self.frame_size = frame_size
        self.callback = callback
        self.connect()
    
    def connect(self):
        """
        connect to rabbitmq server and declare exchange and queue.
        """
        parameters = pika.ConnectionParameters(virtual_host=self.virtual_host,
                        credentials=pika.PlainCredentials(self.username, self.password),
                        frame_max=self.frame_size,
                        host=self.mq_server, heartbeat_interval=60)
        
        self.connection = TornadoConnection(parameters=parameters,
                                            on_open_callback=self.on_connected)
        
    def on_connected(self, _connection):
        _connection.channel(self.on_channel_open)
    
    def on_channel_open(self, _channel):
        self.channel = _channel
        self.channel.exchange_declare(exchange='nagios',
                                              type='fanout',
                                              durable=True,
                                              callback=self.on_exchange_declared)

    def on_exchange_declared(self, _exchange):
        self.channel.queue_declare(durable=False, exclusive=True,
                                           callback=self.on_queue_declared)
    
    def on_queue_declared(self, _result):
        self.queue_name = _result.method.queue
        self.channel.queue_bind(exchange='nagios',
                                        queue=self.queue_name,
                                        callback=self.on_queue_bind)
    
    def on_queue_bind(self, _frame):
        self.channel.basic_consume(self.handle_delivery,
                                           queue=self.queue_name)
    
    def handle_delivery(self, ch, method, header, body):
        if self.callback:
            self.callback(ch, method, header, body)


if __name__ == '__main__':
    # make simple test
    
    def print_body(ch, method, header, body):
        print body
    
    from tornado.ioloop import IOLoop
    
    mq_host = "127.0.0.1"
    mq_username = "guest"
    mq_password = "guest"
    mq_virtual_host = "/"
    
    NagiosReceiver(mq_host, mq_username, mq_password, mq_virtual_host, callback=print_body)
    IOLoop.instance().start()
    
