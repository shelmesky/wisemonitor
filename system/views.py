#!--encoding:utf-8--

import os
import sys

import motor
from tornado import web
from tornado import gen

from settings import MOTOR_DB as DB
from common.init import WiseHandler
from common.decorator import require_login


class Physical_Device_Alerts(WiseHandler):
    @web.asynchronous
    @gen.coroutine
    @require_login
    def get(self):
        alerts = []
        cursor = DB.alerts.find({"type": "physical_device"})
        
        while(yield cursor.fetch_next):
            alert = cursor.next_object()
            alerts.append(alert)
        
        alerts.reverse()
        
        self.render("system/system_alerts_physical_device.html", alerts=alerts)


class XenServer_Alerts(WiseHandler):
    @web.asynchronous
    @gen.coroutine
    @require_login
    def get(self):
        alerts = []
        cursor = DB.alerts.find({"type": "xenserver"})
        
        while(yield cursor.fetch_next):
            alert = cursor.next_object()
            alerts.append(alert)
            
        alerts.reverse()
        
        self.render("system/system_alerts_xenserver.html", alerts=alerts)


class CloudStack_Alerts(WiseHandler):
    @require_login
    def get(self):
        pass
    