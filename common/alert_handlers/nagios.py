import os
import time
import json
from settings import MOTOR_DB as DB


def nagios_alert_handler(ch, method, header, data, pipe):
    try:
        data = json.loads(data)
    except Exception, e:
        return False
    
    def insert_callback(result, err):
        os.write(pipe, "nagios: " + repr(result))
    
    message_type = data['message_type']
    if message_type == "service_check" or message_type == "host_check":
        message = data['data']
        return_code = message['return_code']
        if return_code != 0:
            msg = {
                'type': 'physical_device',
                'message_type': message_type,
                'created_time': time.ctime(),
                'message': {
                    'host': message['host'],
                    'service': message.get('service', ''),
                    'return_code': message['return_code'],
                    'output': message['output']
                }
            }
            DB.alerts.insert(msg, callback=insert_callback)

