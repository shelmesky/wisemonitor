import re
import time


def xenserver_event_handler(host, event, session, mongo_executer):
    msg = {
        'type': 'xenserver',
        'created_time': time.ctime()
    }
    
    operation = event['operation']
    if operation == "add":
        if "snapshot" in event.keys():
            snapshot = event['snapshot']
    
        body = snapshot['body']
        
        vm_uuid = snapshot['obj_uuid']
        vm = session.xenapi.VM.get_by_uuid(vm_uuid)
        name_label = session.xenapi.VM.get_name_label(vm)
        
        msg['message'] = {}
        msg['message']['vm_name_label'] = name_label
        msg['message']['vm_ref_id'] = vm
        msg['message']['host'] = host
        
        for item in body.split('\n'):
            name_str = re.search(".*name.*\"(.*)\"", item)
            value_str = re.search("\w+:\s(.*)", item)
            trigger_value_str = re.search(".*level.*\"(.*)\"", item)
            
            if name_str:
                msg['message_type'] = name_str.groups()[0]
            
            if value_str:
                msg['message']['current_value'] = value_str.groups()[0]
                
            if trigger_value_str:
                msg['message']['trigger_value'] = trigger_value_str.groups()[0]
        
        mongo_executer.insert("alerts", msg)

