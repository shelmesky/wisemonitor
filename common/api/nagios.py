#!/usr/bin/env python
#!--encoding:utf-8--

import os
import subprocess

from pynag import Model
from pynag.Parsers import config

NAGIOS_MAIN_CONF = "/etc/nagios3/nagios.cfg"
NAGIOS_CONF_DIR = "/etc/nagios3/conf.d/"
NAGIOS_STATS_BIN = "/usr/sbin/nagios3stats"
NAGIOS_PROGRAM_BIN = "/usr/sbin/nagios3"
commands = {}


def get_all_commands():
    if commands:
        return commands
    nc = config(NAGIOS_MAIN_CONF)
    nc.parse()
    all_command = nc.data['all_command']
    for command in all_command:
        commands[command['command_name']] = command['command_line']

get_all_commands()


def get_host_by_host_name(host_name):
    """
    通过主机名查找主机
    @host_name主机名
    正常返回一个主机对象
    """
    Model.cfg_file = NAGIOS_MAIN_CONF
    Model.Parsers.config().parse()
    if host_name:
        hosts = Model.Host.objects.filter(host_name=host_name)
        if len(hosts) == 1:
            return hosts[0]
        else:
            return False
    return False


def get_host_by_address(address):
    """
    通过IP地址查找主机
    @address主机IP地址
    正常返回一个主机对象
    """
    Model.cfg_file = NAGIOS_MAIN_CONF
    Model.Parsers.config().parse()
    if address:
        hosts = Model.Host.objects.filter(address=address)
        if len(hosts) == 1:
            return hosts[0]
        else:
            return False
    return False


def add_host(**kwargs):
    """
    增加一个nagios主机，增加后重启nagios进程
    @host_name 主机名
    @alias 主机的别名
    @address 主机的IP地址
    @use 主机使用的模板，如不指定，默认使用generic-host
    """
    if os.getuid() != 0:
        return False, RuntimeError("need root privileges.")
    
    host_name = kwargs.get("host_name", "")
    alias = kwargs.get("alias", "")
    address = kwargs.get("address", "")
    use = kwargs.get("use", "")
    
    if not address or not host_name:
        return False, RuntimeError("address or host_name is empty.")
    
    if not alias:
        alias = host_name
    
    if not use:
        use = "generic-host"
    
    if get_host_by_address(address):
        return False, RuntimeError("address is duplicate!.")
    
    if host_name and address:
        filename = NAGIOS_CONF_DIR + address + "_" + host_name + ".cfg"
        
    new_host = Model.Host(filename=filename)
    new_host.host_name = host_name
    new_host.alias = alias
    new_host.address = address
    new_host.use = use
    
    new_host.save()
    return True, None


def delete_host(host_object):
    """
    删除主机对象
    应该由delete_host_by_xxx函数调用
    """
    try:
        host_object.delete()
    except Exception, e:
        return False, e
    else:
        return True, None


def delete_host_by_host_name(host_name):
    """
    根据主机名删除主机
    """
    host = get_host_by_host_name(host_name)
    if host:
        result, err = delete_host(host)
        return result, err
    return False, RuntimeError("can not find host by host_name.")


def delete_host_by_host_address(address):
    """
    根据主机IP地址删除主机
    """
    host = get_host_by_address(address)
    if host:
        result, err = delete_host(host)
        return result, err
    return False, RuntimeError("can not find host by address.")


def get_service(address, service_desc=None):
    """
    根据主机IP地址获取主机的服务
    如指定了service_desc，则获取相应的服务
    address 主机的IP地址
    service_desc 服务的描述
    正常返回一个服务对象
    """
    Model.cfg_file = NAGIOS_MAIN_CONF
    Model.Parsers.config().parse()
    
    host = get_host_by_address(address)
    if host:
        host_name = host.host_name
        if address and service_desc==None:
            service = Model.Service.objects.filter(host_name=host_name)
            if service:
                return service
        if address and service_desc:
            service = Model.Service.objects.filter(host_name=host_name,
                                                   service_description=service_desc)
            if service:
                return service


def add_service(**kwargs):
    """
    为主机增加服务，增加配置文件后，重启nagios进程
    @address 主机IP地址
    @service_description 服务的描述
    @check_command 要执行的检测命令
    @filename 主机的配置文件名
    """
    if os.getuid() != 0:
        return False, RuntimeError("need root privileges.")
    
    address = kwargs.get("address", "")
    service_description = kwargs.get("service_description", "")
    use = kwargs.get("use", "")
    check_command = kwargs.get("check_command", "")
    filename = kwargs.get("filename", "")
    
    if not use:
        use = "generic-service"
    
    host = get_host_by_address(address)
    if not host:
        return False, RuntimeError("can not find any host.")
    
    if not filename:
        filename = host.get_filename()
    
    if not service_description or not check_command:
        return False, RuntimeError("missed argument.")

    new_service = Model.Service(filename=filename)
    new_service.service_description = service_description
    new_service.use = use
    new_service.check_command = check_command
    new_service.host_name = host.host_name
    new_service.save()
    
    _, err = restart_nagios_process()
    if err != None:
        raise err
    
    return True, None


def restart_nagios_process():
    """
    重启nagios进程
    根据nagios3stats命令获得nagios3主进程PID
    发送HUP信号给nagios3主进程
    """
    if os.getuid() != 0:
        return False, RuntimeError("need root privileges.")
    if not os.path.exists(NAGIOS_STATS_BIN):
        return False, RuntimeError("can not find nagios3stats")
    if not os.path.exists(NAGIOS_PROGRAM_BIN):
        return False, RuntimeError("can not find nagios3")
    
    process = subprocess.Popen(NAGIOS_STATS_BIN, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    process.wait()
    if process.returncode != 0:
        return False, RuntimeError("can not execute nagios3stats")
    nagios3_stats = process.stdout.readlines()
    
    nagios3_pid = None
    try:
        for line in nagios3_stats:
            if 'PID' in line:
                nagios3_pid = line.split(":")[1].strip()
                break
    except Exception, e:
        return False, RuntimeError("can not get PID for nagios3")
    else:
        kill_hup = "kill -HUP %s" % nagios3_pid
        process = subprocess.Popen(kill_hup, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        process.wait()
        if process.returncode != 0:
            return False, RuntimeError("can not restart nagios3")
    
        return True, None
