#!/usr/bin/env python

import sys
from subprocess import Popen
import settings


try:
    import kule
    import bottle
except ImportError:
    print "Can not find kule or bottle module, exit now."
    sys.exit(1)

bind = "0.0.0.0:1983"
mongodb_host = settings.MONGO_HOST
database = settings.MONGO_DB_NAME
collectiosn = """alerts, nagios_host_perfdata,
nagios_host_status,nagios_hosts,
nagios_instance,nagios_objects,
nagios_service_perfdata,
nagios_service_status,nagios_services,virtual_host"""
collectiosn = collectiosn.replace("\n", "")

log_file = settings.API_SERVER_LOG
log_fd = open(log_file, "a+")

stdout = log_fd
stderr = log_fd

python = "/usr/bin/python"
kule_args = " -m kule --bind=%s --mongodb-host=%s --database %s --collections %s"
kule = kule_args % (bind, mongodb_host, database, collectiosn)
args = python + kule

kule_process = Popen([args], shell=True, stdout=stdout, stderr=stderr)
try:
    print "start api server."
    kule_process.wait()
except KeyboardInterrupt:
    print "api server exit now."
