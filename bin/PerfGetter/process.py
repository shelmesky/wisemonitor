#!--encoding:utf-8--

import time
import re
import math

from gevent import hub

from convert import converter
from logger import logger


cpu_usage_re = re.compile("^cpu\d+$")
network_rx_re = re.compile("^vif_\d+_rx$")
network_tx_re = re.compile("^vif_\d+_tx$")
disk_read_re = re.compile("^vbd_\w+_read$")
disk_write_re = re.compile("^vbd_\w+_write$")

vms_performance_list = {}


def init_uuid(uuid):
    if not vms_performance_list.get(uuid):
        vms_performance_list[uuid] = {}


def save_cpu_usage(uuid, data):
    init_uuid(uuid);
    vms_performance_list[uuid]['cpu_usage'] = data


def save_network_io(uuid, data):
    init_uuid(uuid);
    vms_performance_list[uuid]['network_io'] = data


def save_disk_io(uuid, data):
    init_uuid(uuid);
    vms_performance_list[uuid]['disk_io'] = data


def insert_sort(l, get_key):
    l.insert(0, None)
    i = 2
    while i <= len(l)-1:
        if get_key(l[i]) < get_key(l[i-1]):
            l[0] = l[i]
            
            j = i-1
            while get_key(l[j]) > get_key(l[0]):
                l[j+1] = l[j]
                j-=1
            l[j+1] = l[0]
            
        i+=1
        
    l.pop(0)


def process(thread_queue):
    from api.mongo_api import MongoExecuter
    from api.mongo_driver import db_handler
    from api.mongo_driver import conn
    c = MongoExecuter(db_handler)
    
    while 1:
        try:
            action_type, data = thread_queue.get()
            item = converter(data)
        except hub.LoopExit:
            print "process exit..."
            return
        
        thread_queue.task_done()
        
        for vm in item:
            data = vm['data']
            uuid = vm['uuid']
            
            cond = {"type": action_type, "uuid": uuid}
            ret = c.query_one("virtual_host", cond)
            
            record = {
                "data": {},
                "uuid": uuid,
                "type": action_type,
                "timestamp": str(int(time.time()))
            }
            
            cpu_usage = []
            network_io = []
            disk_io = []
            
            for data_field, value in data.items():
                temp_lsit = []
                for item_val in value:
                    temp = {}
                    temp['last_update'] = str(item_val['last_update'])
                    temp['data'] = float(item_val['data'])
                    temp['timestamp'] = long(item_val['timestamp'])
                    temp_lsit.append(temp)
                record['data'][data_field] = temp_lsit
                
                
                if re.match(cpu_usage_re, data_field):
                    if not math.isnan(temp['data']):
                        cpu_usage.append(temp['data'])
                    
                if re.match(network_rx_re, data_field) or re.match(network_tx_re, data_field):
                    if not math.isnan(temp['data']):
                        network_io.append(temp['data'])
                    
                if re.match(disk_read_re, data_field) or re.match(disk_write_re, data_field):
                    if not math.isnan(temp['data']):
                        disk_io.append(temp['data'])
            
            
            # 保存每台虚拟机的CPU负载/网卡IO/磁盘IO性能参数
            cpu_usage_data = 0
            if len(cpu_usage) > 0:
                for i in cpu_usage:
                    cpu_usage_data += i
                try:
                    cpu_usage_data = cpu_usage_data / len(cpu_usage)
                except:
                    pass
            
            network_io_data = 0
            if len(network_io) > 0:
                for i in network_io:
                    network_io_data += i
                try:
                    network_io_data = network_io_data / len(network_io)
                except:
                    pass
            
            disk_io_data = 0
            if len(disk_io) > 0:
                for i in disk_io:
                    disk_io_data += i
                try:
                    disk_io_data = int(disk_io_data / len(disk_io))
                except:
                    pass
            
            save_cpu_usage(uuid, cpu_usage_data)
            save_network_io(uuid, network_io_data)
            save_disk_io(uuid, disk_io_data)
            
            if not ret:
                c.insert("virtual_host", record)
            else:
                c.update("virtual_host", cond, record)
