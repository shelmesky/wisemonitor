#!--encoding:utf-8--

import os
import re
import time
import json
import datetime
from tornado import ioloop

from logger import logger
from common import binproto
from common.api import pipe
from common.api.comet_processor import Reader
from common import utils


def xenserver_event_handler(host, event, session, mongo_executer):
    t = datetime.datetime.now()
    t = datetime.datetime(t.year, t.month, t.day, t.hour, t.minute, t.second)
    msg = {
        'type': 'xenserver',
        'created_time': t
    }
    
    operation = event.get('operation', None)
    klass = event.get('class', None)
    if operation == "add" and klass == "message":
        if "snapshot" in event.keys():
            snapshot = event['snapshot']
        
        if snapshot['name'] != "ALARM":
            return
    
        body = snapshot['body']
        
        vm_uuid = snapshot['obj_uuid']
        vm = session.xenapi.VM.get_by_uuid(vm_uuid)
        name_label = session.xenapi.VM.get_name_label(vm)
        
        msg['message'] = {}
        msg['message']['vm_name_label'] = name_label
        msg['message']['vm_ref_id'] = vm
        msg['message']['host'] = host
        
        error_count = 0
        for item in body.split('\n'):
            name_str = re.search(".*name.*\"(.*)\"", item)
            value_str = re.search("\w+:\s(.*)", item)
            trigger_value_str = re.search(".*level.*\"(.*)\"", item)
            
            if name_str:
                msg['message_type'] = name_str.groups()[0]
                error_count += 1
            
            if value_str:
                msg['message']['current_value'] = value_str.groups()[0]
                error_count += 1
                
            if trigger_value_str:
                msg['message']['trigger_value'] = trigger_value_str.groups()[0]
                error_count += 1
            
        
        if error_count == 3:
            obj_id = mongo_executer.insert("alerts", msg)
            msg.pop("_id")
            msg["created_time"] = utils.time_stamp_to_string(time.time())
            
            source = "xen"
            obj_id = str(obj_id)
            body = json.dumps(msg)
            body_length = len(body)
            # 管道中发送的数据，使用简单的协议封装
            data = binproto.pack(source, obj_id, body_length)
            if data:
                xen_read, xen_write = pipe.make_xen_pipe()
                
                os.write(xen_write, data)
                logger.info("*" * 100)
                logger.info("Send xenserver head: (%s, %s, %s)" % (source, obj_id, body_length))
                
                os.write(xen_write, body)
                logger.info("Send xenserver body: ")
                logger.info(body)
                
                reader = Reader(xen_read, xen_write)
                io_loop = ioloop.IOLoop.instance()
                io_loop.add_handler(xen_read, reader.data_processor, io_loop.READ)
        else:
            logger.error("Error occurred when get event from xenserver:")
            logger.error(str(event))

