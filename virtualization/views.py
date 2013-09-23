import os
import sys
import json

from tornado import web

from common.init import *
from common.api.mongo_driver import db_handler as wise_db_handler
from common.api.mongo_api import MongoExecuter

from xenserver import get_xenserver_host
from xenserver import get_xenserver_host_all
from xenserver import get_xenserver_vm_all
from logger import logger

import settings


class XenServer_VMs_Chart_Handler(WiseHandler):
    def get(self, uuid, ttype):
        executer = MongoExecuter(wise_db_handler)
        result = executer.query("virtual_host", {"uuid": uuid, "type": ttype})
        for data in result:
            self.write(json.dumps(data))


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
        self.render("virtualization/xenserver_console.html",
                    novnc_host=settings.NOVNC_SERVER_IP,
                    novnc_port = settings.NOVNC_SERVER_PORT,
                    vm_ref=vm_ref, host_address=host)

