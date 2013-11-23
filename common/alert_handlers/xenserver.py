import os
import re
import time
import json
from logger import logger


def xenserver_event_handler(host, event, session, mongo_executer, pipe):
    msg = {
        'type': 'xenserver',
        'created_time': time.ctime()
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
            os.write(pipe, "xen^" + str(obj_id) + "^" + json.dumps(msg))
        else:
            logger.error("Error occurred when get event from xenserver:")
            logger.error(str(event))

