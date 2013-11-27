#!/usr/bin/env python
#!--encoding:utf-8--

import struct


BIN_FORMAT = "<64s128sL"

def pack(source, obj_id, body_length):
    if len(source) > 64:
        return None
    if len(obj_id) > 128:
        return None
    data = struct.pack(BIN_FORMAT, source, obj_id, body_length)
    return data


def unpack(data):
    try:
        source, obj_id, body_length = struct.unpack(BIN_FORMAT, data)
        source = source.replace('\x00', '')
        obj_id = obj_id.replace('\x00', '')
        return source, obj_id, body_length
    except Exception, e:
        return None, None, None


def get_pack_size():
    return struct.calcsize(BIN_FORMAT)
