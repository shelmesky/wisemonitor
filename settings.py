#!/usr/bin/env python
# -- coding: utf-8--
import motor

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

MOTOR_CLIENT = motor.MotorClient(MONGO_URI, MONGO_PORT).open_sync()
MOTOR_DB = MOTOR_CLIENT[MONGO_DB_NAME]

CHART_COLORS = [
                "#666699",
                "#003366",
                "#99ccff",
                "#333399",
                "#336699",
                "#0099ff",
                "#0099cc",
                "666666",
                "#669999",
                "#333366",
                "#990033",
                "#663366",
                "#993333",
				"#ff9999",
				"#cc3399",
				"#ff6600",
				"#993366",
				"#ff0033"
				"#99cccc",
                ]

XENSERVER_CHART_DISABLED_FIELDS = ["inflight", "avgqu", "iops", "internal"]

try:
    from local_conf import *
except:
    pass
