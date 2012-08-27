import time

from xenserver.host import XenRRDHost
from xenserver.parsers import RRDUpdates
from settings import COLLECTOR_START_SECONDS_AGO


def collect_rrd_updates(xen_server, username, password, start=None):
    xen = XenRRDHost(xen_server, username, password)

    if start is None:
        start = int(time.time() - COLLECTOR_START_SECONDS_AGO)

    rrd_xml = xen.fetch_rrd_updates(start)
    return RRDUpdates(rrd_xml)
