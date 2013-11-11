#!--encoding:utf-8--

from views import *
url_handlers = [
# 列出所有的zone
(r"^/cloudform/virtualstack/$", CloudStack_Zone_Handler),

# 列出zone的详细信息，包括pad,cluster,host,系统vm,使用量列表
# 参数: cloudstack主机/zone
(r"^/cloudform/virtualstack/([^/]+)/([^/]+)/detail/$", CloudStack_Zone_Detail_Handler),

# 列出zone的使用量信息
# 参数: cloudstack主机/zone
(r"^/cloudform/virtualstack/([^/]+)/([^/]+)/capacity/$", CloudStack_Zone_Capacity_Handler),

# 列出所有的pod
# 参数: cloudstack主机/zone
(r"^/cloudform/virtualstack/([^/]+)/([^/]+)/pod/$", CloudStack_Pod_Handler),

# 列出所有的cluster
# 参数：cloudstack主机/zone
(r"^/cloudform/virtualstack/([^/]+)/([^/]+)/cluster/$", CloudStack_Cluster_Handler),

# 列出所有的host
# 参数: cloudstack主机/zone
(r"^/cloudform/virtualstack/([^/]+)/([^/]+)/host/$", CloudStack_Host_Handler),

# 列出所有的用户级vm
# 参数：cloudstack主机/zone
(r"^/cloudform/virtualstack/([^/]+)/([^/]+)/vm/$", CloudStack_VM_Handler),

# 列出所有的系统级vm
# 参数：cloudstack主机/zone
(r"^/cloudform/virtualstack/([^/]+)/([^/]+)/sysvm/$", CloudStack_VM_Handler),

#(r"/cloudform/openstack", OpenStack_Handler),
]
