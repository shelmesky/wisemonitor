"""Tools for importing RRD data.

Class:
    MongoDBImporter
"""

import time
from pymongo import Connection

from xenrrd.host import XenHost, XenRRDHost
from xenrrd.parsers import RRDUpdates


class MongoDBImporter(object):
    """Importer for MongoDB.

    Methods:
        import_rrd_updates: import 'rrd_updates' data from a XenRRDHost
    """

    def __init__(self, db_host, db_name,
                 vm_info='vm_info', vm_metrics='vm_metrics',
                 host_info='host_info', host_metrics='host_metrics'):
        """Construct a MongoDBImporter object.

        :param db_host: MongoDB host string
        :param db_name: name of the database
        :param vm_info: name of the collection to store vm info
        :param vm_metrics: name of the collection to store vm metrics
        :param host_info: name of the collection to store xen host info
        :param host_metrics: name of the collection to store xen host metrics
        """

        connection = Connection(db_host)
        db = connection[db_name]
        self.vm_info = db[vm_info]
        self.vm_metrics = db[vm_metrics]
        self.host_info = db[host_info]
        self.host_metrics = db[host_metrics]

    def import_rrd_updates(self, xen_rrd_host, start=None):
        """Import VM metrics from a Xen host.

        The data points step is determined by Xen host, based on 'start'.
        Minimal step supported by Xen host is 5 seconds, with 10 minutes' data.

        :param xen_rrd_host: the XenRRDHost to get VM metrics data
        :param start: start time (seconds from epoch) of the data points.
                      If None, use time of last data points in collection.
                      If no data points exist, use 10 minutes ago as start.
        """

        host_doc = self.host_info.find_one({'host': xen_rrd_host.host})
        if host_doc is None:
            host_doc = {'host': xen_rrd_host.host}

        if start is None:
            if host_doc.get('last_rrd_updates', None) is None:
                start = int(time.time() - 10 * 60)  # 10 mintues ago
            else:
                start = host_doc['last_rrd_updates'] + 1  # the next data point

        rrd_xml = xen_rrd_host.fetch_rrd_updates(start)
        rrd_updates = RRDUpdates(rrd_xml)

        def insert(record):
            record['cf'] = rrd_updates.cf
            record['step'] = rrd_updates.step
            record['_id'] = '{uuid}:{epoch_time}:{cf}:{step}'.format(**record)

            host_or_vm = record.pop('host_or_vm', None)
            if host_or_vm == 'host':
                record['name'] = xen_rrd_host.host
                self.host_metrics.save(record)
            if host_or_vm == 'vm':
                record['host'] = xen_rrd_host.host
                record['name'] = self._get_name_label(xen_rrd_host,
                                                      record['uuid'])
                self.vm_metrics.save(record)

        map(insert, rrd_updates.records)

        host_doc['last_rrd_updates'] = rrd_updates.end
        self.host_info.save(host_doc)

    def _get_name_label(self, xen_rrd_host, uuid):
        vm_doc = self.vm_info.find_one({'uuid': uuid})
        if vm_doc:
            return vm_doc.get('name')

        # Create an XenHost object context
        with XenHost(xen_rrd_host.host, xen_rrd_host.username,
                     xen_rrd_host.password, follow_master=True) as xen_host:
            vm = xen_host.find_one_vm(uuid=uuid, exclude_control_domain=False)

        if vm is not None:
            vm_name = vm.get('name_label')

            # Save vmname for later retrieval
            vm_doc = self.vm_info.find_one({'name': vm_name})
            if vm_doc:
                self.vm_info.update(vm_doc, {'$push': {'uuid': uuid}})
            else:
                vm_doc = {'name': vm_name, 'uuid': [uuid]}
                self.vm_info.save(vm_doc)

            return vm_name

        return None
