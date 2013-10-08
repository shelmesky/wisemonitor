#!/usr/bin/env python
# -- coding: utf-8--

XENSERVER_ENABLED = True

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

APPS = (
    "infrastracture",
    "virtualization",
    "platform",
)

XEN = (
    ("192.2.3.44", "root", "0x55aa",),
    ("192.2.4.10", "root", "123456",),
)

NOVNC_SERVER_IP = "192.2.3.188"
NOVNC_SERVER_PORT = 19999

THREADS_MAPREDUCE = 4

try:
    from local_conf import *
except:
    pass
