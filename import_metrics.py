"""Utilities for Xen metrics.

Functions:
    import_metrics
"""

import time
from pymongo import Connection

from xenrrd.host import XenRRDHost
from xenrrd.parsers import RRDUpdates


class MongoDBImporter(object):
    def __init__(self, db_host, db_name,
                 metrics_collection, host_collection='hosts'):
        connection = Connection(db_host)
        db = connection[db_name]
        self.metrics_collection = db[metrics_collection]
        self.host_collection = db[host_collection]

    def import_metrics(self, xen_rrd_host, start=None):
        """Import VM metrics from a Xen host.

        The data points step is determined by Xen host, based on 'start'.
        Minimal step supported by Xen host is 5 seconds, with 10 minutes' data.

        :param xen_rrd_host: the XenRRDHost to get VM metrics data
        :param start: start time (seconds from epoch) of the data points.
                      If None, use time of last data points in collection.
                      If no data points exist, use 10 minutes ago as start.
        """

        host = self.host_collection.find_one({'host': xen_rrd_host.host})
        if host is None:
            host = {'host': xen_rrd_host.host}

        if start is None:
            if host.get('last_rrd_updates', None) is None:
                start = int(time.time() - 10 * 60)  # 10 mintues ago
            else:
                start = host['last_rrd_updates'] + 1  # the next data point

        rrd_xml = rrd_host.fetch_rrd_updates(start)
        rrd_updates = RRDUpdates(rrd_xml)

        def insert(record):
            record['cf'] = rrd_updates.cf
            record['step'] = rrd_updates.step
            record['host'] = rrd_host.host
            record['_id'] = '{uuid}:{epoch_time}:{cf}:{step}'.format(**record)
            self.metrics_collection.save(record)

        map(insert, rrd_updates.records)

        host['last_rrd_updates'] = rrd_updates.end
        self.host_collection.save(host)
