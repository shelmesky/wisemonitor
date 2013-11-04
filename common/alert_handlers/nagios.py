import json
from settings import MOTOR_DB as DB


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
                'message': {
                    'host': message['host'],
                    'service': message['service'] if message['service'] else "",
                    'return_code': message['return_code'],
                    'output': message['output']
                }
            }
            DB.nagios_alerts.insert(msg)

