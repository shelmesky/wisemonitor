#!--encoding:utf-8--
import os

xenserver_waiters = {}
xenserver_msg_cache = []

nagios_waiters = {}
nagios_msg_cache = []


def data_processor(fd, events):
    data = os.read(fd, 4096)
    print data
