#!--encoding:utf-8--

import os
import sys
import json

from tornado import web
from tornado import gen

from common.init import *
from common.utils import get_chart_colors

from xenserver import get_vm_info
from xenserver import get_xenserver_host
from xenserver import get_xenserver_host_all
from xenserver import get_xenserver_vm_all
from xenserver import get_vm_info_by_uuid
from xenserver import get_control_domain
from xenserver import get_xenserver_conn
from utils import parse_perfmon_xml
from utils import general_perfmon_xml
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
    if not record:
        callback(None)
    all_records = record['data']
    final_data['uuid'] = record['uuid']
    final_data['type'] = record['type']
    
    #根据预先定义的颜色值，设置每个数据字段的颜色
    colors = get_chart_colors()
    
    # 填充keys
    for key in all_records.keys():
        has_disabled_filed = False
        for field in chart_disabled_fields:
            if field in key:
                has_disabled_filed = True
                break
        if has_disabled_filed:
            continue
        final_data['data'][key] = {}
        final_data['data'][key]['data'] = []
        final_data['data'][key]['color'] = colors.pop()
        
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
            final_data['data'][key]['data'].append([time, data])
    
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
        if not vm_record:
            control_domain_ref = get_control_domain(self.host)
            control_domain_ref = control_domain_ref.split(":")[1]
            vm_record = get_vm_info(self.host, control_domain_ref)
        vm_name = vm_record['name_label']
        
        self.render("virtualization/xenserver_vm_chart.html",
                    data=data, xenserver_address=self.host,
                    vm_uuid=self.uuid, chart_type=self.ttype, vm_name=vm_name)


class XenServer_VM_Perfmon(WiseHandler):
    def get(self, xen_host, vm_ref):
        session = get_xenserver_conn(xen_host)
        if session != None:
            vm_info = get_vm_info(xen_host, vm_ref)
            record = session.xenapi.VM.get_record("OpaqueRef:" + vm_ref)
            try:
                perfmon = record['other_config']['perfmon']
            except Exception, e:
                perfmon = None
            if perfmon:
                data = parse_perfmon_xml(perfmon)
                self.render("virtualization/xenserver_vm_perfmon.html",
                            data=data, host_address=xen_host,
                            vm_ref=vm_ref, vm_info=vm_info)
            else:
                self.render("virtualization/xenserver_vm_perfmon.html",
                            data=None, host_address=xen_host,
                            vm_ref=vm_ref, vm_info=vm_info)
    
    def post(self, xen_host, vm_ref):
        global_period = self.get_argument("global_period", None, strip=True)
        global_period = int(global_period) * 60 if global_period else None
        
        cpu_level = self.get_argument("cpu_level", None, strip=True)
        cpu_level = float(float(cpu_level) / 100) if cpu_level else None
        
        cpu_period = self.get_argument("cpu_period", None, strip=True)
        cpu_period = int(cpu_period) * 60 if cpu_period else None
        
        network_level = self.get_argument("network_level", None, strip=True)
        network_level = int(network_level) * 1024 if network_level else None
        
        network_period = self.get_argument("network_period", None, strip=True)
        network_period = int(network_period) * 60 if network_period else None
        
        disk_level = self.get_argument("disk_level", None, strip=True)
        disk_level = int(disk_level) * 1024 if disk_level else None
        
        disk_period = self.get_argument("disk_period", None, strip=True)
        disk_period = int(disk_period) * 60 if disk_period else None
        
        data = {
            "global_period": global_period,
            "cpu_level": cpu_level,
            "cpu_period": cpu_period,
            "network_level":  network_level,
            "network_period": network_period,
            "disk_level": disk_level,
            "disk_period": disk_period
        }
        
        perfmon_xml = general_perfmon_xml(data)
        perfmon_xml = perfmon_xml.replace("\n", "")
        perfmon_xml = perfmon_xml.replace("\t", "")
        
        session = get_xenserver_conn(xen_host)
        if session != None:
            try:
                session.xenapi.VM.remove_from_other_config("OpaqueRef:" + vm_ref, "perfmon")
                session.xenapi.VM.add_to_other_config("OpaqueRef:" + vm_ref, "perfmon", perfmon_xml)
            except Exception, e:
                raise e
            else:
                vm_info = get_vm_info(xen_host, vm_ref)
                record = session.xenapi.VM.get_record("OpaqueRef:" + vm_ref)
                try:
                    perfmon = record['other_config']['perfmon']
                except Exception, e:
                    perfmon = None
                if perfmon:
                    data = parse_perfmon_xml(perfmon)
                    self.render("virtualization/xenserver_vm_perfmon.html",
                                data=data, host_address=xen_host,
                                vm_ref=vm_ref, vm_info=vm_info)
                else:
                    self.render("virtualization/xenserver_vm_perfmon.html",
                                data=None, host_address=xen_host,
                                vm_ref=vm_ref, vm_info=vm_info)


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

