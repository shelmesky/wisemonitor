#!--encoding:utf-8--
import os
import json
import errno
from tornado.ioloop import IOLoop

from logger import logger
import comet_backend
from common import binproto
from logger import logger
from common.api.sms_client import send_sms


class Reader(object):
    def __init__(self, read_fd, write_fd):
        self.ioloop = IOLoop.instance()
        self.head = None
        self.body = None
        self.source = None
        self.obj_id = None
        self.body_length = None
        self.read_fd = read_fd
        self.write_fd = write_fd
    
    def read_head(self):
        # 管道中发送的数据，使用简单的协议封装
        self.pack_size = binproto.get_pack_size()
        try:
            self.head = os.read(self.fd, self.pack_size)
        except Exception as e:
            if e[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
                self.ioloop.add_handler(self.fd, self.data_processor, self.ioloop.READ)
            else:
                logger.exception(e)
        else:
            self.process_head()
    
    def process_head(self):
        if len(self.head) == self.pack_size:
            try:
                self.source, self.obj_id, self.body_length = binproto.unpack(self.head)
            except Exception as e:
                logger.exception(e)
            else:
                logger.info("Got head: (%s %s %s)" % (self.source, self.obj_id, self.body_length))
                self.read_body()
        else:
            logger.error("Error occurred while read head, close the pipe.")
            self.ioloop.remove_handler(self.fd)
            self.close_fd()
    
    def read_body(self):
        try:
            data = os.read(self.fd, self.body_length)
        except Exception as e:
            if e[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
                self.ioloop.add_handler(self.fd, self.data_processor, self.ioloop.READ)
            else:
                logger.exception(e)
        else:
            logger.info("Got body: %s" % data)
            if len(data) == self.body_length:
                self.process_body(data)
            else:
                logger.error("Error occurred while read body, close the pipe.")
                self.ioloop.remove_handler(self.fd)
                self.close_fd()

    def data_processor(self, fd, events):
        logger.info("*" * 100)
        logger.info("Receiver got fd: %s events: %s" % (fd, events))
        self.fd = fd
        if not self.head:
            self.read_head()
        else:
            self.read_body()
    
    def process_body(self, data):
        if self.source == "nagios":
            msg = {
                "message_id": self.obj_id,
                "message": json.loads(data)
            }
	    # send sms
	    send_sms(msg['message'], "nagios")
            comet_backend.manager.nagios_insert_msg_cache(msg)
            for user, callback in comet_backend.manager.get_nagios_waiters():
                callback(msg)
            comet_backend.manager.nagios_empty_waiters()
            
        if self.source == "xen":
            msg = {
                "message_id": self.obj_id,
                "message": json.loads(data)
            }
	    # send sms
	    send_sms(msg['message'], "xen")
            comet_backend.manager.xenserver_insert_msg_cache(msg)
            for user, callback in comet_backend.manager.get_xenserver_waiters():
                callback(msg)
            comet_backend.manager.xenserver_empty_waiters()
        
        logger.info("Remove and Close [read fd: %s] [write fd: %s] " % (self.read_fd, self.write_fd))
        self.ioloop.remove_handler(self.fd)
        self.close_fd()
    
    def close_fd(self):
        os.close(self.read_fd)
        os.close(self.write_fd)
