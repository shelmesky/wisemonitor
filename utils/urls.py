#!--encoding:utf-8--

from views import *
url_handlers = [

# xenserver的名字到refid
(r"^/api/xenserver/name_to_refid/$", XenServer_Name_To_RefID),

# xenserver的名字到uuid
(r"^/api/xenserver/name_to_uuid/$", XenServer_Name_To_UUID),
]