#!--encoding:utf-8--

from views import *
url_handlers = [

# 列出所有的zone
(r"^/api/xenserver/name_to_refid/$", XenServer_Name_To_RefID),

]