#!--encoding:utf-8--

import os
import sys
import hashlib
import json
import uuid
import re
import functools
import datetime

import motor
from tornado import web
from tornado import gen
import bson

from settings import MOTOR_DB as DB
from common.init import WiseHandler
from common.decorator import require_login
from common.api import comet_backend
from common import utils
from logger import logger


class Physical_Device_Alerts(WiseHandler):
    @web.asynchronous
    @gen.coroutine
    @require_login
    def get(self):
        keyword = self.get_argument("keyword", "").strip()
        limit = self.get_argument("limit", "")
        page = self.get_argument("page", "")
        
        start_time = self.get_argument("start_time", "")
        end_time = self.get_argument("end_time", "")
        start_time_stamp = end_time_stamp = None
        start_time_cond = end_time_cond = None
        
        if start_time:
            try:
                start_time_stamp = int(utils.time_string_to_stamp(start_time, f="%Y%m%d%H%M%S"))
            except:
                pass
            else:
                start_time_cond = datetime.datetime.fromtimestamp(start_time_stamp)
                
        if end_time:
            try:
                end_time_stamp = int(utils.time_string_to_stamp(end_time, f="%Y%m%d%H%M%S"))
            except:
                pass
            else:
                end_time_cond = datetime.datetime.fromtimestamp(end_time_stamp)
        
        if page:
            try:
                page = int(page)
            except:
                page = 0
        else:
            page = 0
            
        if page == -1:
            page = 0
        
        if limit:
            try:
                limit = int(limit)
            except:
                limit = 10
        else:
            limit = 10
        alerts = []
        
        if start_time_cond and end_time_cond:
            cond = {
                "type": "physical_device",
                "created_time": {"$gte": start_time_cond, "$lte": end_time_cond},
            }
        else:
            cond = {
                "type": "physical_device",
            }
        
        origin_keyword = None
        if keyword:
            origin_keyword = keyword
            if not keyword.startswith("@"):
                cond = {
                    "type": "physical_device",
                    "$or": [
                        {"message.host": re.compile(".*%s.*" % keyword)},
                        {"message.output": re.compile(".*%s.*" % keyword)},
                        {"message.service": re.compile(".*%s.*" % keyword)},
                    ],
                    "created_time": {"$gte": start_time_cond, "$lte": end_time_cond},
                }
            else:
                keyword = keyword[1:]
                if keyword == "warn":
                    cond = {
                        "type": "physical_device",
                        "message.return_code": 1,
                        "created_time": {"$gte": start_time_cond, "$lte": end_time_cond},
                    }
                elif keyword == "critical":
                    cond = {
                        "type": "physical_device",
                        "message.return_code": 2,
                        "created_time": {"$gte": start_time_cond, "$lte": end_time_cond},
                    }
                elif keyword == "unknow":
                    cond = {
                        "type": "physical_device",
                        "message.return_code": 3,
                        "created_time": {"$gte": start_time_cond, "$lte": end_time_cond},
                    }
            
        # 分页开始
        cursor = DB.alerts.find(cond)
        record_count = yield motor.Op(cursor.count)
        cursor = cursor.skip(page * limit).limit(limit)
        
        # 一次最多显示几页
        max_per_page = 10
        
        max_pages = record_count / limit
        if record_count % limit != 0:
            max_pages += 1
        
        # 存储当前显示的页数
        page_elements = []
        start = 0
        end = 0
        
        # 如果总页数大于10，则默认显示到第10页结束
        # 否则直接显示总页数
        if max_pages >= max_per_page:
            end = max_per_page
        else:
            end = max_pages
        
        if page >= max_per_page:
            current_ten_page = page / max_per_page
            start = current_ten_page * max_per_page
            end = start + 10
            
            if end > max_pages:
                remain_page_nums = max_pages % max_per_page
                if remain_page_nums > 0:
                    end = start + remain_page_nums
        
        for i in range(start, end):
            page_elements.append(i)
        
        current_page = page
        prev_page = current_page - 1
        next_page = current_page + 1
        # 分页结束
        
        while(yield cursor.fetch_next):
            alert = cursor.next_object()
            alerts.append(alert)
        
        alerts.reverse()
        
        # add page id for every client
        page_id = str(uuid.uuid4())
        if not self.get_secure_cookie("page_id", None) :
            self.set_secure_cookie("page_id", page_id)
        
        self.render("system/system_alerts_physical_device.html",
                    alerts=alerts, limit=limit, keyword=origin_keyword,
                    real_pages=page_elements,
                    max_pages=max_pages-1,
                    min_pages=0,
                    current_page=current_page,
                    prev_page=prev_page,
                    next_page=next_page,
                    start_time=start_time,
                    end_time=end_time)
    
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
        keyword = self.get_argument("keyword", "").strip()
        limit = self.get_argument("limit", "")
        page = self.get_argument("page", "")
        
        if page:
            try:
                page = int(page)
            except:
                page = 0
        else:
            page = 0
        
        if page == -1:
            page = 0
        
        if limit:
            try:
                limit = int(limit)
            except:
                limit = 10
        else:
            limit = 10
        alerts = []
        
        cond = {
            "type": "xenserver",
        }
        
        origin_keyword = None
        if keyword:
            origin_keyword = keyword
            if not keyword.startswith("@"):
                cond = {
                    "type": "xenserver",
                    "$or": [
                        {"message.host": re.compile(".*%s.*" % keyword)},
                        {"message.vm_name_label": re.compile(".*%s.*" % keyword)},
                    ]
                }
            else:
                keyword = keyword[1:]
                if keyword == "disk":
                    cond = {
                        "type": "xenserver",
                        "message_type": "disk_usage"
                    }
                elif keyword == "cpu":
                    cond = {
                        "type": "xenserver",
                        "message_type": "cpu_usage"
                    }
                elif keyword == "network":
                    cond = {
                        "type": "xenserver",
                        "message_type": "network_usage"
                    }
        else:
                cond = {
                    "type": "xenserver",
                }
            
        # 分页开始
        cursor = DB.alerts.find(cond)
        record_count = yield motor.Op(cursor.count)
        cursor = cursor.skip(page * limit).limit(limit)
        
        # 一次最多显示几页
        max_per_page = 10
        
        max_pages = record_count / limit
        if record_count % limit != 0:
            max_pages += 1
        
        # 存储当前显示的页数
        page_elements = []
        start = 0
        end = 0
        
        # 如果总页数大于10，则默认显示到第10页结束
        # 否则直接显示总页数
        if max_pages >= max_per_page:
            end = max_per_page
        else:
            end = max_pages
        
        if page >= max_per_page:
            current_ten_page = page / max_per_page
            start = current_ten_page * max_per_page
            end = start + 10
            
            if end > max_pages:
                remain_page_nums = max_pages % max_per_page
                if remain_page_nums > 0:
                    end = start + remain_page_nums
        
        for i in range(start, end):
            page_elements.append(i)
        
        current_page = page
        prev_page = current_page - 1
        next_page = current_page + 1
        # 分页结束
        
        while(yield cursor.fetch_next):
            alert = cursor.next_object()
            alerts.append(alert)
        
        alerts.reverse()
        
        # add page id for every client
        page_id = str(uuid.uuid4())
        if not self.get_secure_cookie("page_id", None) :
            self.set_secure_cookie("page_id", page_id)
        
        self.render("system/system_alerts_xenserver.html",
                    alerts=alerts, limit=limit, keyword=origin_keyword,
                    real_pages=page_elements,
                    max_pages=max_pages-1,
                    min_pages=0,
                    current_page=current_page,
                    prev_page=prev_page,
                    next_page=next_page)
    
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
    
