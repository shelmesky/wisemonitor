#!/usr/bin/python
# --encoding:utf-8--

import pymongo
import settings
from logger import logger

class MongoDBDriver(object):
    def __init__(self, mongo_uri, **kwargs):
        self.mongo_uri = mongo_uri
        self.conn_pool_size = kwargs.get("conn_pool_size", 512)
        self.conn_timeout = kwargs.get("conn_timeout", 2)
    
    def connect(self):
        '''
        返回mongodb的连接对象
        '''
        try:
            self.connection = pymongo.MongoClient(host=self.mongo_uri,
                                                max_pool_size=self.conn_pool_size,
                                                connectTimeoutMS=self.conn_timeout)
        except Exception, e:
            logger.exception(e)
            raise
        logger.debug("Connecto to mongodb %s" % self.mongo_uri)
    
    def close(self):
        self.connection.close()


driver = MongoDBDriver(settings.MONGO_URI,
                       conn_pool_size=settings.MONGO_CONN_POOL_SIZE,
                       conn_timeout=settings.MONGO_CONN_TIMEOUT)
driver.connect()
conn = driver.connection
# db的连接对象
db_handler = conn[settings.MONGO_DB_NAME]

