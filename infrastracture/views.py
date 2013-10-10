#! --encoding: utf-8--
import os
import sys
import json
import re

from tornado import web
from tornado import gen
from settings import MOTOR_DB as DB

import motor

from common.init import WiseHandler
from common.api.mongo_driver import db_handler as wise_db_handler
from common.api.mongo_api import MongoExecuter
from common.utils import get_four_hours_ago, get_one_day_ago
from common.utils import get_one_week_ago, get_one_year_ago


class Infra_Server_Handler(WiseHandler):
    @web.asynchronous
    @gen.coroutine
    def get(self):
        cursor = DB.nagios_hosts.find()
            
        ret = dict()
        ret['objects'] = list()
        i = 1
        
        while(yield cursor.fetch_next):
            host = cursor.next_object()
            temp = dict()
            host_object_id = host['object_id']
            cursor_one = DB.nagios_host_status.find({"object_id": host['object_id']})
            yield cursor_one.fetch_next
            host_status = cursor_one.next_object()
            temp['id'] = i
            temp['_id'] = str(host_object_id)
            temp['host_name'] = host['host_name']
            temp['host_address'] = host['host_address']
            temp['notification_period'] = host['host_notification_period']
            temp['state'] = host_status['state']
            temp['return_code'] = host_status['return_code']
            temp['last_update'] = host_status['last_update']
            temp['output'] = host_status['output']
            i += 1
            ret['objects'].append(temp)
            
        ret['objects'].sort(key=lambda x: x['_id'])
        self.render("infrastracture/server.html", server_list=ret['objects'])


class Infra_Server_Services_Handler(WiseHandler):
    @web.asynchronous
    @gen.coroutine
    def get(self, ip):
        cursor = DB.nagios_hosts.find({"host_address": ip})
        yield cursor.fetch_next
        host = cursor.next_object()
        
        cursor_one = DB.nagios_service_status.find({"host": host['host_name']})
            
        ret = dict()
        ret['objects'] = list()
        i = 1
        while(yield cursor_one.fetch_next):
            service = cursor_one.next_object()
            temp = dict()
            temp['_id'] = str(service['object_id'])
            temp['id'] = i
            temp['host_name'] = service['host']
            temp['service_name'] = service['service']
            temp['state'] = service['state']
            temp['return_code'] = service['return_code']
            temp['output'] = service['output']
            temp['last_update'] = service['last_update']
            i += 1
            ret['objects'].append(temp)
            
        ret['objects'].sort(key=lambda x: x['_id'])
        self.render("infrastracture/services.html", services_list=ret['objects'], host_ip=ip)


def parse_perfdata(original_data, frequency=1):
    """
    根据frequency(频率)计算平均值
    每段数据的时间点，取每段的第一条数据
    """
    fields_data = {}
    
    # 获取性能数据的字段
    fields = []
    for record in original_data:
        perf_data = record['perf_data']
        for item in perf_data:
           field = item['field']
           fields.append(field)
        break
    
    # 预先填充字段名
    for field in fields:
        fields_data[str(field)] = {}
        fields_data[str(field)]['data'] = []
    
    final_data = []
    for r in original_data:
        final_data.append(r)
    data_length = original_data.count()
    
    for i in xrange(0, data_length, frequency):
        start = i
        if start >0:
            start = start - 1
        end = i + frequency
        
        temp_data = {}
        for f in fields:
            temp_data[str(f)] = 0
        
        temp_timestamp = final_data[start]['last_update']
        
        for record in final_data[start:end]:
            perf_data = record['perf_data']
            for item in perf_data:
                field = str(item['field'])
                data = item['data'][0]
                
                # 如果记录中已经存在字段的'别名'
                if "field_alias" in item:
                    fields_data[field]['field_alias'] = item['field_alias']
                        
                # 如果数据的'单位'已经存在与记录中
                if "unit" in item:
                    unit = item['unit']
                else:
                    unit = re.match(r".*\d(.*)", data).groups()[0]
                fields_data[field]['unit'] = str(unit)
                
                # 替换数据中的'单位'字符串为空格
                temp_data[field] += float(data.replace(unit, ""))
            
        for k,v in temp_data.items():
            fields_data[k]['data'].append([temp_timestamp, v/frequency])
        
    return fields_data


class Infra_Server_Chart_Handler(WiseHandler):
    def get(self, host, chart_type):
        collection_perfdata = "nagios_host_perfdata"
        collection_hosts = "nagios_hosts"
        
        if not chart_type or not host:
            self.send_error(404)
        
        if chart_type == "4h":
            ago = get_four_hours_ago()
            frequency = 1
        elif chart_type == "24h":
            ago = get_one_day_ago()
            frequency = 4
        elif chart_type == "1w":
            ago = get_one_week_ago()
            frequency = 12
        elif chart_type == "1y":
            ago = get_one_year_ago()
        else:
            ago = None
        
        if chart_type != "1y":
            executer = MongoExecuter(wise_db_handler)
            
            if ago:
                result = executer.query_one(collection_hosts, {"host_address": host})
                object_id = result['object_id']
                data = executer.query(collection_perfdata, {"object_id": object_id, "timestamp": {"$gte": ago}})
            
                fields_data = parse_perfdata(data, frequency)
                #print >> sys.stderr, json.dumps(fields_data)
            else:
                self.send_error(500)
        else:
            pass
        
        self.render("infrastracture/server_chart.html", host=host,
                    chart_type=chart_type, data=json.dumps(fields_data))
    
    
class Infra_Service_Chart_Handler(WiseHandler):
    def get(self, host, service, chart_type):
        pass

