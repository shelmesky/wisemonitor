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
    "cloudform",
	"utils",
    "system"
)

XEN = (
    ("192.2.3.44", "root", "0x55aa",),
    ("192.2.4.10", "root", "123456",),
)

XENSERVER_CONNECT_TIMEOUT = 2 #seconds

NOVNC_SERVER_IP = "192.2.3.188"
NOVNC_SERVER_PORT = 19999

THREADS_MAPREDUCE = 4

USE_THIS_MOTOR = False

if USE_THIS_MOTOR:
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
                "#669999",
                "#333366",
                "#990033",
                "#663366",
                "#993333",
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
                ]

XENSERVER_CHART_DISABLED_FIELDS = ["inflight", "avgqu", "iops", "internal"]

CLOUD_STACKS = (
    {
        "host": "http://192.2.4.47:8080",
        "api_key": "7jMTaFbgPUNvJxrYenL49Fy7VqPxjD47vh8tGKnHnez3xhVYf85QX-E5CL7TGmZrX-q9f__xyhQp4UV7Y7W36A",
        "secret_key": "otwkgDSRGauj8OX7EGfwGtWZWIJjpm98UurRE_EAwJmdhvwbcB8tBdTbx4ftmkhM9MOsCLIkILbUsO2KCWFitA"
    },
)

# set timeout for connect and request with cloudstack client
CLOUDSTACK_CONNECT_TIMEOUT = 2
CLOUDSTACK_REQUEST_TIMEOUT = 2

NAGIOS_HANDLE_ENABLED = True

MQ_HOST = "127.0.0.1"
MQ_USERNAME = "guest"
MQ_PASSWORD = "guest"
MQ_VIRTUAL_HOST = "/"

XENSERVER_HANDLE_ENABLED = True

API_SERVER_LOG = "api_server.log"

# Check SNMP Interface command in Nagios
NAGIOS_CHECK_SNMP_INT_COMMAND = "check_snmp_int_v2"

# VNC Playback Server
VNC_PLAYBACK_SERVER_IP = "127.0.0.1"
VNC_PLAYBACK_SERVER_PORT = 23456

# Perf Rand Server
PERF_RANK_SERVER_IP = "127.0.0.1"
PERF_RANK_SERVER_PORT = 23458


try:
    from local_conf import *
except Exception, e:
    raise e
