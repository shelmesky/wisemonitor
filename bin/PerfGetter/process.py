import time

from gevent import hub

from convert import converter
from logger import logger


def process(thread_queue):
    from api.mongo_api import MongoExecuter
    from api.mongo_driver import db_handler
    from api.mongo_driver import conn
    c = MongoExecuter(db_handler)
    
    while 1:
        try:
            action_type, data = thread_queue.get()
            item = converter(data)
        except hub.LoopExit:
            print "process exit..."
            return
        
        thread_queue.task_done()
        
        for vm in item:
            data = vm['data']
            uuid = vm['uuid']
            
            cond = {"type": action_type, "uuid": uuid}
            ret = c.query_one("virtual_host", cond)
            
            record = {
                "data": {},
                "uuid": uuid,
                "type": action_type,
                "timestamp": str(int(time.time()))
            }
            
            for data_field, value in data.items():
                temp_lsit = []
                for item_val in value:
                    temp = {}
                    temp['last_update'] = str(item_val['last_update'])
                    temp['data'] = float(item_val['data'])
                    temp['timestamp'] = long(item_val['timestamp'])
                    temp_lsit.append(temp)
                record['data'][data_field] = temp_lsit
            
            if not ret:
                c.insert("virtual_host", record)
            else:
                c.update("virtual_host", cond, record)
