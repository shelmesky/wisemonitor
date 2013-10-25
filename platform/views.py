#!--encoding:utf-8--

import os
import sys
import json

from tornado import web
from tornado import gen

from common.init import WiseHandler

from common.api import CloudStack as cloudstack_api

import settings


def get_cs_conn(cs):
    for cs_host in settings.CLOUD_STACKS:
        if cs == cs_host['host']:
            host = 'http://' + cs_host['host'] + ':' + cs_host['port']
            client = cloudstack_api.Client(host, cs_host['api_key'], cs_host['secret_key'])
            return client


class CloudStack_Zone_Handler(WiseHandler):
    """
    列出所有的zone
    """
    @gen.coroutine
    @web.asynchronous
    def get(self):
        zones = []
        for cs_host in settings.CLOUD_STACKS:
            temp = {}
            host = 'http://' + cs_host['host'] + ':' + cs_host['port']
            client = cloudstack_api.Client(host, cs_host['api_key'], cs_host['secret_key'])
            result = yield client.listZones()
            temp['data'] = result
            temp['cs_host'] = cs_host['host']
            zones.append(temp)
            
        self.render("platform/cloudstack_zones.html", data=zones)


class CloudStack_Zone_Detail_Handler(WiseHandler):
    """
    列出zone的详细信息
    包括pod,cluster,host,系统vm的列表,使用量信息
    
    参数：
    @cs CloudStack的主机
    @zone_id zone的ID
    """
    @gen.coroutine
    @web.asynchronous
    def get(self, cs, zone_id):
        client = get_cs_conn(cs)
        if client:
            pods = yield client.listPods(zoneid=zone_id)
            clusters = yield client.listClusters(zoneid=zone_id)
            hosts = yield client.listHosts(zoneid=zone_id)
            vms = yield client.listVirtualMachines(zoneid=zone_id)
            sysvms = yield client.listSystemVms(zoneid=zone_id)
            
            zone = yield client.listZones(id=zone_id)
            zone_name = zone['listzonesresponse']['zone'][0]['name']
    
            final_data = {
                'pods': pods,
                'clusters': clusters,
                'hosts': hosts,
                'vms': vms,
                'sysvms': sysvms,
                'zone_name': zone_name,
                'cs_host': cs
            }
            
            self.write(json.dumps(final_data))
            self.finish()


class CloudStack_Pod_Handler(WiseHandler):
    """
    列出所有的pod
    
    参数：
    @cs CloudStack的主机
    @zonei_d Zone的ID
    """
    @web.asynchronous
    @gen.coroutine
    def get(self, cs, zone_id):
        client = get_cs_conn(cs)
        if client:
            pods = yield client.listPods(zoneid=zone_id)
            
            zone = yield client.listZones(id=zone_id)
            zone_name = zone['listzonesresponse']['zone'][0]['name']
            
            final_data = {
                'pods': pods,
                'zone_name': zone_name,
                'cs_host': cs
            }
            
            self.write(json.dumps(final_data))
            self.finish()


class CloudStack_Cluster_Handler(WiseHandler):
    """
    列出所有的cluster
    
    参数：
    @cs CloudStack的主机
    @zone_id Zone的ID
    """
    def get(self, cs, zone_id):
        pass


class CloudStack_Host_Handler(WiseHandler):
    """
    列出所有的host
    
    参数：
    @cs CloudStack的主机
    @zone_id Zone的ID
    @pod_id Pod的ID
    @cluster_id Cluster的ID
    """
    def get(self, cs, zone_id, pod_id, cluster_id):
        pass


class CloudStack_VM_Handler(WiseHandler):
    """
    列出所有的vm
    
    参数：
    @cs CloudStack的主机
    @zone_id Zone的ID
    @pod_id Pod的ID
    @cluster_id Cluster的ID
    @host_id Host的ID
    """
    def get(self, cs, zone_id, pod_id, cluster_id, host_id):
        pass

