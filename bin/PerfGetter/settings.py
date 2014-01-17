#!/usr/bin/env python
# -- coding: utf-8--

LOG_PATH = "server.log"
LOG_INSTANCE = "Server"

# configuration for MongoDB
MONGO_HOST = "127.0.0.1"
MONGO_PORT = 27017
MONGO_USERNAME = None
MONGO_PASSWORD = None
MONGO_DB_NAME = "wisemonitor"
MONGO_CONN_POOL_SIZE = 10
MONGO_CONN_TIMEOUT = 2000 #ms

if MONGO_USERNAME:
    MONGO_URI = "mongodb://" + MONGO_USERNAME + ((":" + MONGO_PASSWORD + "@") \
        if MONGO_PASSWORD else "@") \
        + MONGO_HOST + ":" + str(MONGO_PORT) + "/" + MONGO_DB_NAME
else:
    MONGO_URI = MONGO_HOST

XEN = (
    ("192.2.3.44", "root", "0x55aa",),
)

try:
    from local_conf import *
except Exception, e:
    raise e
