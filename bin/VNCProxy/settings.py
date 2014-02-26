#!/usr/bin/env python
# -- coding: utf-8--

LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 19999

LOG_PATH = "server.log"
LOG_INSTANCE = "Server"

XEN = (
    ("192.2.3.44", "root", "0x55aa",),
    ("192.2.4.10", "root", "123456",),
)

# VNC Record Server
VNC_RECORD_SERVER_IP = "127.0.0.1"
VNC_RECORD_SERVER_PORT = 23457

try:
    from local_conf import *
except:
    pass
