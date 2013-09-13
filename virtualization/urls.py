from views import *

url_handlers = [
# list all xenservers
#(r"/virtual/xenserver", XenServer_Handler),
# vm list of one xenserver
# the arguments are: ip address of xenserver
#(r"/virtual/xenserver/(.*)/vms", XenServer_VMs_Handler),
# charts of one vm
# the arguments are: host/uuid/chart type
(r"/virtual/xenserver/hosts/", XenServer_Get_ALL),
(r"/virtual/xenserver/(.*)/vms/", XenServer_Get_ALL_vms),
(r"/virtual/xenserver/(.*)/chart/(.*)/", XenServer_VMs_Chart_Handler),

#(r"/virtual/libvirt", Libvirt_Handler),
]