"""Parsers for Xen RRD in XML format."""

import xml.etree.ElementTree
from collections import defaultdict, OrderedDict, namedtuple


_LegendEntry = namedtuple('_LegendEntry',
                          ['cf', 'host_or_vm', 'uuid', 'metric_name'])


class RRDUpdates(object):
    def __init__(self, rrd_xml):
        """Construct a RRDUpdates object for parsed rrd_updates result.

        :param rrd_xml: rrd_updates result XML
        :type rrd_xml: string
        """

        self._parse(rrd_xml)

    @property
    def records(self):
        """Return an iterator of records

        A record include epoch_time of the data, uuid of VM and metrics,
        where metrics can include data for CPUs, Network Interfaces, Memeries
        and Block Devices, etc.
        """

        result = defaultdict(OrderedDict)

        for row in self.data.iter('row'):
            epoch_time = int(row.find('t').text)

            for i, v in enumerate(row.iter('v')):
                legend_entry = self.legend_entries[i]

                value = float(v.text)

                record = result[(epoch_time, legend_entry.uuid,
                                 legend_entry.host_or_vm)]
                record[legend_entry.metric_name] = value

            # All columns of the row processed now.
            # And 'result' populated with records.
            # We can begin yield individual result
            while result:
                key, metrics = result.popitem()
                epoch_time, uuid, host_or_vm = key
                yield {'epoch_time': epoch_time,
                       'uuid': uuid,
                       'host_or_vm': host_or_vm,
                       'metrics': metrics}

    def _parse(self, rrd_xml):
        xport = xml.etree.ElementTree.fromstring(rrd_xml)
        meta = xport.find('meta')
        self.data = xport.find('data')

        self.start = int(meta.find('start').text)
        self.step = int(meta.find('step').text)
        self.end = int(meta.find('end').text)
        self.rows = int(meta.find('rows').text)
        self.columns = int(meta.find('columns').text)

        legend = meta.find('legend')
        self.legend_entries = [_LegendEntry._make(entry.text.split(':'))
                               for entry in legend.iter('entry')]

        try:
            # We're assuming cf in all legend entries are same
            self.cf = self.legend_entries[0].cf
        except IndexError:
            pass
