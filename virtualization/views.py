#!--encoding:utf-8--

import os
import sys
import json

from tornado import web
from tornado import gen

from common.init import *

from xenserver import get_vm_info
from xenserver import get_xenserver_host
from xenserver import get_xenserver_host_all
from xenserver import get_xenserver_vm_all
from xenserver import get_vm_info_by_uuid
from logger import logger

import settings
from settings import MOTOR_DB as DB
from settings import XENSERVER_CHART_DISABLED_FIELDS

chart_disabled_fields = XENSERVER_CHART_DISABLED_FIELDS


@gen.coroutine
def parse_perfdata(cursor, callback):
    final_data = {}
    final_data['data'] = {}
    yield cursor.fetch_next
    record = cursor.next_object()
    all_records = record['data']
    final_data['uuid'] = record['uuid']
    final_data['type'] = record['type']
    
    # 填充keys
    for key in all_records.keys():
        has_disabled_filed = False
        for field in chart_disabled_fields:
            if field in key:
                has_disabled_filed = True
                break
        if has_disabled_filed:
            continue
        final_data['data'][key] = []
        
    # 填充数据
    for key, items in all_records.items():
        has_disabled_filed = False
        for field in chart_disabled_fields:
            if field in key:
                has_disabled_filed = True
                break
        if has_disabled_filed:
            continue
        for item in items:
            data = float("%1.f" % item['data'])
            time = int(item['timestamp']) * 1000
            final_data['data'][key].append([time, data])
    
    callback(final_data)


class XenServer_VMs_Chart_Handler(WiseHandler):
    @web.asynchronous
    @gen.coroutine
    def get(self, host, uuid, ttype):
        self.uuid = uuid
        self.host = host
        self.ttype = ttype
        cursor = DB.virtual_host.find({"uuid": uuid, "type": ttype})
        yield parse_perfdata(cursor, self.on_parse_finished)
    
    def on_parse_finished(self, data):
        vm_record = get_vm_info_by_uuid(self.host, self.uuid)
        vm_name = vm_record['name_label']
        
        self.render("virtualization/xenserver_vm_chart.html",
                    data=data, xenserver_address=self.host,
                    vm_uuid=self.uuid, chart_type=self.ttype, vm_name=vm_name)


class XenServer_Get_Host(WiseHandler):
    def get(self, xen_host):
        host = get_xenserver_host(xen_host)
        self.render("virtualization/xenserver_host.html", host=host)


class XenServer_Get_ALL(WiseHandler):
    def get(self):
        hosts = get_xenserver_host_all()
        self.render("virtualization/xenserver_all_hosts.html", xenserver_list=hosts)


class XenServer_Get_ALL_vms(WiseHandler):
    def get(self, host):
        vms = get_xenserver_vm_all(host)
        self.render("virtualization/xenserver_all_vms.html", vms=vms, host_address=host)


class XenServer_Get_VM_Console(WiseHandler):
    def get(self, host, vm_ref):
        vm_info = get_vm_info(host, vm_ref)
        self.render("virtualization/xenserver_console.html",
                    novnc_host=settings.NOVNC_SERVER_IP,
                    novnc_port = settings.NOVNC_SERVER_PORT,
                    vm_ref=vm_ref, host_address=host, vm_info=vm_info)

