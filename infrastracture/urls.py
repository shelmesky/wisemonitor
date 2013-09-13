#!/usr/bin/env python
# -- coding: utf-8--
from views import *

# url configuration in here
url_handlers = [
# list all host in nagios
(r"/infra/server/", Infra_Server_Handler),
# list all services for one host in nagios
# the arguments are: ip address of host
(r"/infra/server/(.*)/", Infra_Server_Services_Handler),
]