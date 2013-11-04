import json
from settings import MOTOR_DB as DB


def nagios_alert_handler(data):
    try:
        data = json.loads(data)
    except Exception, e:
        return False
    
    message = data['data']
    return_code = data['return_code']
    if return_code != 0:
        msg = {
            'type': 'physical_device',
            'message_type': data['message_type'],
            'message': {
                'host': message['host'],
                'service': message['service'] if message['service'] else "",
                'return_code': message['return_code'],
                'output': message['output']
            }
        }
        DB.nagios_alerts.insert(msg)

