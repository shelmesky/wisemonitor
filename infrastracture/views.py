import os
import sys
import json

from tornado import web

from common.init import WiseHandler
from common.api.mongo_driver import db_handler as wise_db_handler
from common.api.mongo_api import MongoExecuter


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


class Infra_Server_Chart_Handler(WiseHandler):
    def get(self, host):
        self.render("infrastracture/server_chart.html")
    
    
class Infra_Service_Chart_Handler(WiseHandler):
    def get(self, host, service):
        pass

