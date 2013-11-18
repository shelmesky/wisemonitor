#!--encoding:utf-8--
import os
import json

from logger import logger
import comet_backend


def data_processor(fd, events):
    data = os.read(fd, 4096)
    try:
        source, obj_id = data.split(":")
    except Exception, e:
        logger.exception(e)
        return
    
    if source == "nagios":
        msg = {
            "message_id": obj_id
        }
        comet_backend.manager.nagios_insert_msg_cache(obj_id)
        for user, callback in comet_backend.manager.get_nagios_waiters():
            callback(msg)
        comet_backend.manager.nagios_empty_waiters()
        
    if source == "xen":
        msg = {
            "message_id": obj_id
        }
        comet_backend.manager.xenserver_insert_msg_cache(obj_id)
        for user, callback in comet_backend.manager.get_xenserver_waiters():
            callback(msg)
        comet_backend.manager.xenserver_empty_waiters()
