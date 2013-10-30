#!--encoding:utf-8--

import os
import sys
import json
from pprint import pprint

from tornado import web
from tornado import gen

from common.init import WiseHandler
from virtualization.xenserver import get_vm_info_by_name

import settings


class XenServer_Name_To_RefID(WiseHandler):
    def post(self):
        host_ip = self.get_argument("host", None)
        vm_name = self.get_argument("vm", None)
        
        if not host_ip or not vm_name:
            msg = {
                'state': -1,
                'message': 'need host ip address or vms name'
            }
            self.set_status(403)
            self.write(json.dumps(msg))
            return
        
        ref_id = get_vm_info_by_name(host_ip, vm_name)
        if ref_id:
            msg = {
                'state': 0,
                'message': 'OK',
                'data': {
                    'ref_id': ref_id
                }
            }
            self.write(json.dumps(msg))
            return
        else:
            msg = {
                'state': 1,
                'message': 'error occurred'
            }
            self.set_status(500)
            self.write(json.dumps(msg))
            return

