#!/usr/bin/env python
# -- coding: utf-8--
from views import *

# url configuration in here
url_handlers = [
(r"^/system/alerts/physical_device/$", Physical_Device_Alerts),
(r"^/system/alerts/xenserver/$", XenServer_Alerts),
(r"^/system/alerts/cloudstack/$", CloudStack_Alerts),
]