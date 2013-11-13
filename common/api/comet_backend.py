xenserver_waiters = {}
xenserver_msg_cache = []

nagios_waiters = {}
nagios_msg_cache = []

max_msg_cache = 200

class manager(object):
    @staticmethod
    def nagios_insert_msg_cache(data):
        global nagios_msg_cache
        if len(nagios_msg_cache) > max_msg_cache:
            nagios_msg_cache = []
        nagios_msg_cache.append(data)
    
    @staticmethod
    def get_nagios_waiters():
        global nagios_waiters
        return nagios_waiters.items()
    
    @staticmethod
    def xenserver_insert_msg_cache(data):
        global xenserver_msg_cache
        if len(xenserver_msg_cache) > max_msg_cache:
            xenserver_msg_cache = []
        xenserver_msg_cache.append(data)
    
    @staticmethod
    def get_xenserver_waiters():
        global xenserver_waiters
        return xenserver_waiters.items()
    
    @staticmethod
    def xenserver_empty_waiters():
        global xenserver_waiters
        xenserver_waiters = {}
    
    @staticmethod
    def nagios_empty_waiters():
        global nagios_waiters
        nagios_waiters = {}
    
    @staticmethod
    def get_nagios_msg_cache():
        global nagios_msg_cache
        return nagios_msg_cache
    
    @staticmethod
    def get_xenserver_msg_cache():
        global xenserver_msg_cache
        return xenserver_msg_cache
    
