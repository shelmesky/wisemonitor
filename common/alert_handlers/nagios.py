#!--encoding:utf-8--

import os
import time
import json
from tornado import ioloop
import datetime

from settings import MOTOR_DB as DB
from logger import logger
from common import binproto
from common.api import pipe
from common.api.comet_processor import Reader
from common import utils


def nagios_alert_handler(ch, method, header, data):
    try:
        data = json.loads(data)
    except Exception, e:
        return False
    
    message_type = data['message_type']
    if message_type == "service_check" or message_type == "host_check":
        message = data['data']
        return_code = message['return_code']
        if return_code != 0:
            msg = {
                'type': 'physical_device',
                'message_type': message_type,
                'created_time': datetime.datetime.now(),
                'message': {
                    'host': message['host'],
                    'service': message.get('service', ''),
                    'return_code': message['return_code'],
                    'output': message['output']
                }
            }
            
            def insert_callback(result, err):
                # motor will add "_id" to the original data
                msg.pop("_id")
                msg["created_time"] = utils.time_stamp_to_string(time.time())
                
                source = "nagios"
                obj_id = str(result)
                body = json.dumps(msg)
                body_length = len(body)
                # 管道中发送的数据，使用简单的协议封装
                data = binproto.pack(source, obj_id, body_length)
                if data:
                    nagios_read, nagios_write = pipe.make_nagios_pipe()
                    
                    os.write(nagios_write, data)
                    logger.info("*" * 100)
                    logger.info("Send nagios head: (%s, %s, %s)" % (source, obj_id, body_length))
                    
                    os.write(nagios_write, body)
                    logger.info("Send nagios body: ")
                    logger.info(body)
                    
                    reader = Reader(nagios_read, nagios_write)
                    io_loop = ioloop.IOLoop.instance()
                    io_loop.add_handler(nagios_read, reader.data_processor, io_loop.READ)
                
            DB.alerts.insert(msg, callback=insert_callback)

