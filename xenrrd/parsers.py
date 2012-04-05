"""Parsers for Xen RRD in XML format."""

import xml.etree.ElementTree
from collections import namedtuple, OrderedDict


_LegendEntry = namedtuple('_LegendEntry',
                          ['cf', 'host_or_vm', 'uuid', 'metric_name'])


def parse_rrd_updates(rrd_xml):
    """
    Parse XML fetched from 'rrd_updates' and return an iterator.

    :param rrd_xml: the raw xml of the RRD
    :type rrd_xml: string
    :returns: an iterator of key/value pairs, where key is (epoch_time, uuid)
              of the record and value is a dictionary of metrics
    """

    xport = xml.etree.ElementTree.fromstring(rrd_xml)
    meta = xport.find('meta')
    data = xport.find('data')

    row_num = int(meta.find('rows').text)
    colum_num = int(meta.find('columns').text)

    legend = meta.find('legend')
    legend_entries = [_LegendEntry._make(entry.text.split(':'))
                      for entry in legend.iter('entry')]

    from collections import defaultdict
    result = defaultdict(OrderedDict)

    for row in data.iter('row'):
        epoch_time = int(row.find('t').text)

        for i, v in enumerate(row.iter('v')):
            legend_entry = legend_entries[i]

            value = float(v.text)

            record = result[(epoch_time, legend_entry.uuid)]
            record[legend_entry.metric_name] = value

        while result:
            key, metrics = result.popitem()
            epoch_time, uuid = key
            yield {'epoch_time': epoch_time,
                   'uuid': uuid,
                   'metrics': metrics}
