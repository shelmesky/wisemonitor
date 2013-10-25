#!--encoding:utf-8--

from views import *
url_handlers = [
# 列出所有的zone
(r"^/platform/cloudstack/$", CloudStack_Zone_Handler),

# 列出zone的详细信息，包括pad,cluster,host,系统vm,使用量列表
(r"^/platform/cloudstack/([^/])/detail/$", CloudStack_Zone_Detail_Handler),

# 列出所有的pod
# 参数: zone
(r"^/platform/cloudstack/([^/])/$", CloudStack_Pod_Handler),

# 列出所有的cluster
# 参数：zone/pod
(r"^/platform/cloudstack/([^/])/([^/])/$", CloudStack_Cluster_Handler),

# 列出所有的host
# 参数: zone/pod/cluster
(r"^/platform/cloudstack/([^/])/([^/])/([^/])/$", CloudStack_Host_Handler),

# 列出所有的用户级vm
# 参数：zone/pod/cluster/host
(r"^/platform/cloudstack/([^/])/([^/])/([^/])/([^/])/$", CloudStack_VM_Handler),

#(r"/platform/openstack", OpenStack_Handler),
]