#!--encoding:utf-8--

import os
import sys
import hashlib
import json
import uuid

import motor
from tornado import web
from tornado import gen
import bson

from settings import MOTOR_DB as DB
from common.init import WiseHandler
from common.decorator import require_login
from common.api import comet_backend
from logger import logger


class Physical_Device_Alerts(WiseHandler):
    @web.asynchronous
    @gen.coroutine
    @require_login
    def get(self):
        limit = self.get_argument("limit", "")
        if limit:
            try:
                limit = int(limit)
            except:
                limit = 10
        else:
            limit = 10
        alerts = []
        cursor = DB.alerts.find({"type": "physical_device"}).limit(limit)
        
        while(yield cursor.fetch_next):
            alert = cursor.next_object()
            alerts.append(alert)
        
        alerts.reverse()
        
        # add page id for every client
        page_id = str(uuid.uuid4())
        if not self.get_secure_cookie("page_id", None) :
            self.set_secure_cookie("page_id", page_id)
        
        self.render("system/system_alerts_physical_device.html", alerts=alerts, limit=limit)
    
    @require_login
    @web.asynchronous
    def post(self):
        post_from = self.get_argument("post_from", "").strip()
        
        if post_from == "ajax":
            cursor = self.get_argument("cursor", None)
            if cursor != "null":
                index = 0
                msg_cache = comet_backend.manager.get_nagios_msg_cache()
                for i in xrange(len(msg_cache)):
                    index = len(msg_cache) - i - 1
                    if msg_cache[index]['message_id'] == cursor:
                        break
                
                recent = msg_cache[index + 1:]
                if len(recent) > 0:
                    logger.info("Got recent alerts for nagios.")
                    self.on_new_message(recent)
                    return
            
            # use page id for every client to set the callback
            user_page_id = self.get_secure_cookie("page_id")
            user_md5 = hashlib.md5(user_page_id).hexdigest()
            comet_backend.nagios_waiters[user_md5] = self.on_new_message
            
        elif post_from == "form":
            #TODO: 无法使用motor查询，否则无法使用self.finish
            keyword = self.get_argument("search_keyword", "").strip()
    
    def on_new_message(self, data):
        if data:
            if not isinstance(data, list):
                self.finish(json.dumps([data]))
            else:
                self.finish(json.dumps(data))
    
    def on_find_finish(self, alerts, limit):
        self.render("system/system_alerts_physical_device.html", alerts=alerts, limit=limit)
    

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
        
        # add page id for every client
        page_id = str(uuid.uuid4())
        if not self.get_secure_cookie("page_id", None) :
            self.set_secure_cookie("page_id", page_id)
        
        self.render("system/system_alerts_xenserver.html", alerts=alerts)
    
    @require_login
    @web.asynchronous
    def post(self):
        cursor = self.get_argument("cursor", None)
        if cursor != "null":
            index = 0
            msg_cache = comet_backend.manager.get_xenserver_msg_cache()
            for i in xrange(len(msg_cache)):
                index = len(msg_cache) - i - 1
                if msg_cache[index]['message_id'] == cursor:
                    break
            
            recent = msg_cache[index + 1:]
            if len(recent) > 0:
                logger.info("Got recent alerts for xenserver.")
                self.on_new_message(recent)
                return
        
        # use page id for every client to set the callback
        user_page_id = self.get_secure_cookie("page_id")
        user_md5 = hashlib.md5(user_page_id).hexdigest()
        comet_backend.xenserver_waiters[user_md5] = self.on_new_message
    
    def on_new_message(self, data):
        if data:
            if not isinstance(data, list):
                self.finish(json.dumps([data]))
            else:
                self.finish(json.dumps(data))
    

class CloudStack_Alerts(WiseHandler):
    @require_login
    def get(self):
        pass
    
