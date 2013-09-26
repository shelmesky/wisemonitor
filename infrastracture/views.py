#! --encoding: utf-8--
import os
import sys
import json
import re

from tornado import web

from common.init import WiseHandler
from common.api.mongo_driver import db_handler as wise_db_handler
from common.api.mongo_api import MongoExecuter
from common.utils import get_two_hours_ago, get_one_day_ago
from common.utils import get_one_week_ago, get_one_year_ago


class Infra_Server_Handler(WiseHandler):
    def get(self):
        executer = MongoExecuter(wise_db_handler)
        hosts = executer.query("nagios_hosts", None)
        ret = dict()
        ret['objects'] = list()
        i = 1
        for host in hosts:
            temp = dict()
            host_object_id = host['object_id']
            host_status = executer.query_one("nagios_host_status", None)
            temp['id'] = i
            temp['_id'] = str(host_object_id)
            temp['host_name'] = host['host_name']
            temp['host_address'] = host['host_address']
            temp['notification_period'] = host['host_notification_period']
            temp['state'] = host_status['state']
            temp['last_update'] = host_status['last_update']
            temp['output'] = host_status['output']
            i += 1
            ret['objects'].append(temp)
            
        ret['objects'].sort(key=lambda x: x['_id'])
        self.render("infrastracture/server.html", server_list=ret['objects'])


class Infra_Server_Services_Handler(WiseHandler):
    def get(self, ip):
        executer = MongoExecuter(wise_db_handler)
        host = executer.query_one("nagios_hosts", {"host_address": ip})
        services = executer.query("nagios_service_status", {"host": host['host_name']})
        ret = dict()
        ret['objects'] = list()
        i = 1
        for service in services:
            temp = dict()
            temp['_id'] = str(service['object_id'])
            temp['id'] = i
            temp['host_name'] = service['host']
            temp['service_name'] = service['service']
            temp['state'] = service['state']
            temp['output'] = service['output']
            temp['last_update'] = service['last_update']
            i += 1
            ret['objects'].append(temp)
            
        ret['objects'].sort(key=lambda x: x['_id'])
        self.render("infrastracture/services.html", services_list=ret['objects'], host_ip=ip)


def parse_perdata(original_data, frequency=1):
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
    
    # 根据采样率，提取数据
    if frequency > 1:
        # 重置cursor
        original_data.rewind()
        data_length = original_data.count()
        final_data = []
        for i in xrange(0, data_length, frequency):
            final_data.append(original_data[i])
    else:
        final_data = original_data
    
    for record in final_data:
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
            data = data.replace(unit, "")
            
            fields_data[field]['data'].append([record['last_update'], float(data)])
            
    return fields_data


class Infra_Server_Chart_Handler(WiseHandler):
    def get(self, host):
        collection = "nagios_host_perfdata"
        
        two_hours_ago = get_two_hours_ago()
        one_day_ago = get_one_day_ago()
        one_week_ago = get_one_week_ago()
        one_year_ago = get_one_year_ago()
        
        executer = MongoExecuter(wise_db_handler)
        
        two_hours_data = executer.query(collection, {"timestamp": {"$gte": two_hours_ago}})
        one_day_data = executer.query(collection, {"timestamp": {"$gte": one_day_ago}})
        
        #fields_data_two_hours = parse_perdata(two_hours_data)
        fields_data_one_day = parse_perdata(one_day_data, frequency=4)
        
        #print >> sys.stderr, json.dumps(fields_data_two_hours)
        print >> sys.stderr, json.dumps(fields_data_one_day)
        self.render("infrastracture/server_chart.html")
    
    
class Infra_Service_Chart_Handler(WiseHandler):
    def get(self, host, service):
        pass

