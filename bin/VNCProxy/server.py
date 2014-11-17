#!/usr/bin/env python
#! --encoding:utf-8--
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2012 Openstack, LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#!/usr/bin/env python

'''
Websocket proxy that is compatible with Openstack Nova.
Leverages websockify by Joel Martin
'''
from gevent import monkey
monkey.patch_all()

import socket
import sys
import struct
import time

import websockify

import xmlrpclib
import XenAPI
import settings
from pprint import pprint

try:
    from urllib.parse import parse_qs, urlparse
except:
    from cgi import parse_qs
    from urlparse import urlparse


class WebSocketProxy(websockify.WebSocketProxy):
    def __init__(self, *args, **kwargs):
        websockify.WebSocketProxy.__init__(self, *args, **kwargs)

    def get_username_password(self, host_ip):
        for xen_host in settings.XEN:
            if xen_host[0] == host_ip:
                return xen_host[1], xen_host[2]
    
    def do_get_target(self, host, vm_ref):
        self.http = "http://"
        self.https = "https://"
        
        console_location = None

        for xen_host in settings.XEN:
            # 检查host参数
            if xen_host[0] == host:
                proxy = xmlrpclib.ServerProxy(self.http + xen_host[0])
                result = proxy.session.login_with_password(xen_host[1], xen_host[2])
                # result["Status"]为"Failure",说明主机为slave,result["ErrorDescription"][1]为其master
                # 使用master重新获取session_id
                if result["Status"] == "Failure":
                    master = result["ErrorDescription"][1]
                    proxy = xmlrpclib.ServerProxy(self.http + master)
                    result = proxy.session.login_with_password(xen_host[1], xen_host[2])
                    session_id = result["Value"]
                    session = XenAPI.Session(self.http + master)
                    account_info = self.get_username_password(master)
                    session.login_with_password(account_info[0], account_info[1])
                else:
                    session_id = result['Value']
                    record = session.xenapi.VM.get_record(vm_ref)
                    session = XenAPI.Session(self.http + xen_host[0])
                    account_info = self.get_username_password(xen_host[0])
                    session.login_with_password(account_info[0], account_info[1])

                record = session.xenapi.VM.get_record(vm_ref)

                if not record['is_a_template'] and not record['is_a_snapshot']:
                    if record['power_state'] == "Running":
                        all_consoles = record['consoles']
                        for console in all_consoles:
                            console_record = session.xenapi.console.get_record(console)
                            # XenServer 6.2同时提供了vt100和rfb协议的console
                            # 我们使用rfb协议
                            if console_record['protocol'] == "rfb":
                                console_location = console_record['location']
                                
                                ref = console_location[console_location.find("/", 8):]
                                protocol = self.http
                                server = xen_host[0]
                                params =  ref + "&session_id=" + session_id
                                print (protocol, server, params, )
                                return (protocol, server, params, )
                    else:
                        return None

    def get_target(self, path):
        """
        @path: 从websocket客户端传递来的path参数
        类似这样: /websockify?host=192.2.3.44&vm_ref=cb7ecb5b-ec4a-c372-30d8-c11c686dc21f
        host: XenServer主机的IP地址
        vm_ref: VM的reference id(注意不是VM实例属性的'uuid'字段)
        """
        args = parse_qs(urlparse(path)[4]) # 4 is the query from url

        if not args.has_key('host') or not len(args['host']):
            raise self.EClose("Host not present")
        
        if not args.has_key('vm_ref') or not len(args['vm_ref']):
            raise self.EClose("VM REF not present")

        host = args['host'][0].rstrip('\n')
        vm_ref_id = args['vm_ref'][0].rstrip('\n')
        vm_ref_str = "OpaqueRef:" + vm_ref_id
        
        protocol, server, params = self.do_get_target(host, vm_ref_str)
        if protocol == self.http:
            port = 80
        else:
            port = 443
        
        return (server, port, params, vm_ref_id, )

    def new_client(self, attached_object):
        """
        Called after a new WebSocket connection has been established.
        """
        # 根据websocket client传递过来的PATH
        # 找到UUID对应的vnc location
        host, port, vnc_location, vm_ref_id = self.get_target(self.path)
        
        # 如果启用了录制VNC数据
        if self.record:
            vm_info_struct = "<64s128s64s128s"
            start_time = str(int(time.time()))
            client_address = attached_object.client_address[0] + ":" +str(attached_object.client_address[1])
            vm_info = struct.pack(vm_info_struct, host, vm_ref_id, start_time, client_address)
            
            fname = "%s_%s_%s.dat" % (host, vm_ref_id, start_time)
            self.msg("Server Recording to '%s'" % fname)
            
            # Send VMInfo to Recorder Server
            self.msg("Send VM info to Record server")
            try:
                record_server_ip = settings.VNC_RECORD_SERVER_IP
                record_server_port = settings.VNC_RECORD_SERVER_PORT
                record_sock = socket.create_connection((record_server_ip, record_server_port), 3)
                record_sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
                rec_fd = record_sock.makefile()
                rec_fd.write(vm_info)
                rec_fd.flush()
                
                # Receive Reply from server
                self.msg("Receive Reply info from Record server")
                vm_info_reply_struct = "<i"
                size = struct.calcsize(vm_info_reply_struct)
                data = rec_fd.read(size)
                reply = struct.unpack(vm_info_reply_struct, data)
            except Exception, e:
                self.msg("Send Error: %s" % e)
            else:
                if reply[0] == 0:
                    self.msg("Start Send VNC Data to Recorder server...")
                    attached_object.rec = rec_fd
                    encoding = "binary"
                else:
                    attached_object.rec = None
             
        # Connect to the target
        self.msg("connecting to: %s:%s" % (
                 host, port))
        # 创建到XenServer的连接
        tsock = self.socket(host, port,
                connect=True)

        # 连接到XenServer并处理返回的头部
        # Handshake as necessary
        tsock.send("CONNECT %s HTTP/1.1\r\n\r\n" %
                    vnc_location)
        
        data = tsock.recv(17)
        data = tsock.recv(24)
        data = tsock.recv(35)
        data = tsock.recv(2)
        
        if self.verbose and not self.daemon:
            print(self.traffic_legend)

        # Start proxying
        try:
            # 将连接到XenServer的socket作为参数传递给do_proxy
            self.do_proxy(tsock, attached_object)
        except:
            if tsock:
                tsock.shutdown(socket.SHUT_RDWR)
                tsock.close()
                self.vmsg("%s:%s: Target closed" % (host, port))
            raise


def run_server():
    host = settings.LISTEN_HOST
    port = settings.LISTEN_PORT
    server = WebSocketProxy(listen_host=host, listen_port=port, verbose=True, record=True)
    server.start_server()


if __name__ == '__main__':
    run_server()
