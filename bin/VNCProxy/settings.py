#!/usr/bin/env python
# -- coding: utf-8--

LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 19999

LOG_PATH = "server.log"
LOG_INSTANCE = "Server"

XEN = (
    ("172.31.11.113", "root", "SPvm123*!",),
    ("172.31.11.114", "root", "SPvm123*!",),
    ("172.31.11.115", "root", "SPvm123*!",),
    ("172.31.11.116", "root", "SPvm123*!",),
    ("172.31.11.117", "root", "SPvm123*!",),
    ("172.31.11.118", "root", "SPvm123*!",),
    ("172.31.11.119", "root", "SPvm123*!",),
    ("172.31.11.120", "root", "SPvm123*!",),
    ("172.31.11.121", "root", "SPvm123*!",),
)

# VNC Record Server
VNC_RECORD_SERVER_IP = "127.0.0.1"
VNC_RECORD_SERVER_PORT = 23457

try:
    from local_conf import *
except:
    pass
