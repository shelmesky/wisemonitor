import re

from xen_helper import lookup_vm_name_by_uuid


PATH_FMT = 'xen.{host_or_vm}.{name}.{metric_name}{cf_suffix}'
RELEVANT_METRICS_PREFIX = {
    'cpu': '',   # default ('') is average
    'vif_': '',
    'pif_': '',
    'vbd_': '',
}


def write_metrics_pickle(graphite_cli, records):
    """Write metrics to graphite's carbon in pickle protocol.

    Records is an iterator. One record may generate multiple metrics.
    """
    data = []
    for record in records:
        data += _transform(record)
    graphite_cli.send_pickle(data)
    return len(data)


def _transform(record):
    """Retun a list of tuples for use in graphite.

    record is a dict of epoch_time, uuid, host_or_vm, metrics,
    where metrics is a dict of name/value pairs.
    """
    timestamp = record['epoch_time']
    uuid = record['uuid']
    host_or_vm = record['host_or_vm']
    metrics = record['metrics']

    if host_or_vm == 'host':
        name = uuid
    elif host_or_vm == 'vm':
        name = lookup_vm_name_by_uuid(uuid)
    else:  # ignore
        return []

    data = []
    for metric_name, value in metrics.iteritems():
        if _is_relevant(metric_name):
            path = PATH_FMT.format(host_or_vm=host_or_vm,
                                   name=name,
                                   metric_name=metric_name,
                                   cf_suffix=_lookup_suffix(metric_name))
            data.append((path, (timestamp, value)))

    return data


def _is_relevant(metric_name):
    for prefix in RELEVANT_METRICS_PREFIX:
        if metric_name.startswith(prefix):
            return True
    return False


def _lookup_suffix(metric_name):
    for prefix in RELEVANT_METRICS_PREFIX:
        if metric_name.startswith(prefix):
            return RELEVANT_METRICS_PREFIX[prefix]
    return ''
