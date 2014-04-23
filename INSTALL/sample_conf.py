import motor

XENSERVER_ENABLED = True


# configuration for MongoDB
#MONGO_HOST = "172.31.2.189"
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
    ("192.2.4.15", "root", "0x55aa",),
    #("172.31.2.1", "root", "qwe123",),
    #("172.31.2.2", "root", "qwe123",),
    #("172.31.2.3", "root", "qwe123",),
    #("172.31.2.4", "root", "qwe123",),
)


MOTOR_CLIENT = motor.MotorClient(MONGO_URI, MONGO_PORT).open_sync()
MOTOR_DB = MOTOR_CLIENT[MONGO_DB_NAME]


CLOUD_STACKS = (
    {
        "host": "172.31.2.201",
        "port": "8080",
        "api_key": "RMQVCqza1UmrVUKODqDWCYBc1N2hO63fW2KOjRePe2Mp1RLZl_7Yvd967xaZCwkmPhwMSV2l4didilLLJRFqqg",
        "secret_key": "B-FaaDbDkL1fx7vpGvCUL73PolR8v3LOpGDXrtYPQ5OY-cF7P9EcCar5cduju4Pro-M5wNuXuHZSHrsyx0oppA"
    },
)

#MQ_HOST = "172.31.2.189"
MQ_HOST = "127.0.0.1"
MQ_USERNAME = "guest"
MQ_PASSWORD = "guest"
MQ_VIRTUAL_HOST = "/"

#NOVNC_SERVER_IP = "172.31.2.189"
NOVNC_SERVER_IP = "127.0.0.1"
NOVNC_SERVER_PORT = 19999

# VNC Record and Playback
VNC_PLAYBACK_SERVER_IP = "127.0.0.1"
VNC_PLAYBACK_SERVER_PORT = 23456

# Perf Rand Server
PERF_RANK_SERVER_IP = "127.0.0.1"
PERF_RANK_SERVER_PORT = 23458
