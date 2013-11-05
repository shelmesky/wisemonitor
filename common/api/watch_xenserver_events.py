import threading
import motor
import settings
from common.api.mongo_driver import db_handler
from common.api.mongo_api import MongoExecuter


class XenServer_Alerts_Watcher(threading.Thread):
    def __init__(self, host, session, callback=None):
        super(XenServer_Alerts_Watcher, self).__init__()
        self.host = host
        self.callback = callback
        self.session = session
        self.connect_mongo()
    
    def run(self):
        self.session.xenapi.event.register(["*"])
        while True:
            try:
                events = self.session.xenapi.event.next()
                
                for event in events:
                    if event['class'] != 'message': continue
                    if self.callback:
                        self.callback(self.host, event,
                                      self.session, self.mongo_executer)
            
            except XenAPI.Failure, e:
                if e.details <> ["EVENTS_LOST"]:
                    raise
                print "some events may be lost"
                self.session.xenapi.event.unregister(["*"])
                self.session.xenapi.event.register(["*"])
    
    def connect_mongo(self):
        self.mongo_executer = MongoExecuter(db_handler)
