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
    if os.getuid() != 0:
        return False, RuntimeError("need root privileges.")
    
    host_name = kwargs.get("host_name", "")
    alias = kwargs.get("alias", "")
    address = kwargs.get("address", "")
    
    if not address or not host_name:
        return False, RuntimeError("address or host_name is empty.")
    
    if not alias:
        alias = host_name
    
    if get_host_by_address(address):
        return False, RuntimeError("address is duplicate!.")
    
    if host_name and address:
        filename = NAGIOS_CONF_DIR + address + "_" + host_name + ".cfg"
        
    new_host = Model.Host(filename=filename)
    new_host.host_name = host_name
    new_host.alias = alias
    new_host.address = address
    new_host.use = "generic-host"
    
    new_host.save()
    return True, None


def delete_host(host_object):
    try:
        host_object.delete()
    except Exception, e:
        return False, e
    else:
        return True, None


def delete_host_by_host_name(host_name):
    host = get_host_by_host_name(host_name)
    if host:
        result, err = delete_host(host)
        return result, err
    return False, RuntimeError("can not find host by host_name.")


def delete_host_by_host_address(address):
    host = get_host_by_address(address)
    if host:
        result, err = delete_host(host)
        return result, err
    return False, RuntimeError("can not find host by address.")


def restart_nagios_process():
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
    
    kill_hup = "kill -HUP %s" % nagios3_pid
    process = subprocess.Popen(kill_hup, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    process.wait()
    if process.returncode != 0:
        return False, RuntimeError("can not restart nagios3")

    return True, None
