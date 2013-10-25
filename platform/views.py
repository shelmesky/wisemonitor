#!--encoding:utf-8--

import os
import sys
import json

from tornado import web

from common.init import WiseHandler


class CloudStack_Zone_Handler(WiseHandler):
    """
    列出所有的zone
    """
    def get(self):
        pass


class CloudStack_Zone_Detail_Handler(WiseHandler):
    """
    列出zone的详细信息
    包括pod,cluster,host,系统vm的列表,使用量信息
    
    参数：
    @zone_id zone的ID
    """
    def get(self, zone_id):
        pass


class CloudStack_Pod_Handler(WiseHandler):
    """
    列出所有的pod
    
    参数：
    @zonei_d Zone的ID
    """
    def get(self, zone_id):
        pass


class CloudStack_Cluster_Handler(WiseHandler):
    """
    列出所有的cluster
    
    参数：
    @zone_id Zone的ID
    @pod_id Pod的ID
    """
    def get(self, zone_id, pod_id):
        pass


class CloudStack_Host_Handler(WiseHandler):
    """
    列出所有的host
    
    参数：
    @zone_id Zone的ID
    @pod_id Pod的ID
    @cluster_id Cluster的ID
    """
    def get(self, zone_id, pod_id, cluster_id):
        pass


class CloudStack_VM_Handler(WiseHandler):
    """
    列出所有的vm
    
    参数：
    @zone_id Zone的ID
    @pod_id Pod的ID
    @cluster_id Cluster的ID
    @host_id Host的ID
    """
    def get(self, zone_id, pod_id, cluster_id, host_id):
        pass

