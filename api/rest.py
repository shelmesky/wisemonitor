import re
from collections import defaultdict

from bottle import get, request, run
from pymongo import Connection, ASCENDING

import conf


conn = Connection(conf.DB_HOST)
db = conn[conf.DB_NAME]


@get('/vm/<vm_name>/cpu/')
def cpu_metrics(vm_name):
    """Return CPU metrics of the specified VM.

    Time series of data will be provided for each CPU.

    Supported query parameters:
        start (optional) - start time of data points in seconds since epoch
        end (optional) - end time of data points in seconds since epoch

    Example:
        http://localhost/vm/i-4-33-VM/cpu/?start=1334280890&end=1334280910
    """

    result = _query_helper(vm_name, request.query, '^cpu')
    return {'status': 'success', 'result': result}


@get('/vm/<vm_name>/vif/')
def vif_metrics(vm_name):
    """Return VIF (virtual network interface) metrics of the specified VM.

    Time series of data will be provided for each interface and read/write
    combination.

    Supported query parameters:
        start (optional) - start time of data points in seconds since epoch
        end (optional) - end time of data points in seconds since epoch

    Example:
        http://localhost/vm/i-4-33-VM/vif/?start=1334280890&end=1334280910
    """

    result = _query_helper(vm_name, request.query, '^vif_')
    return {'status': 'success', 'result': result}


@get('/vm/<vm_name>/vbd/')
def cpu_metrics(vm_name):
    """Return VBD (virtual block device) metrics of the specified VM.

    Time series of data will be provided for each block device and read/write
    combination.

    Supported query parameters:
        start (optional) - start time of data points in seconds since epoch
        end (optional) - end time of data points in seconds since epoch

    Example:
        http://localhost/vm/i-4-33-VM/vbd/?start=1334280890&end=1334280910
    """

    result = _query_helper(vm_name, request.query, '^vbd_')
    return {'status': 'success', 'result': result}


def _query_helper(vm_name, query, regex=None):
    query_params = {'name': vm_name}

    if regex:
        # Search matching metrics name
        query_params['metrics.name'] = {'$regex': regex}

    # Support 'start' and 'end' request query params
    time_range = defaultdict(dict)
    if query.start:
        time_range['$gte'] = int(request.query.start)
    if query.end:
        time_range['$lte'] = int(request.query.end)
    if time_range:
        query_params['epoch_time'] = time_range

    # Perform the DB search
    docs = db.vm_metrics.find(query_params,
                              ['epoch_time', 'metrics'],
                              sort=[('epoch_time', ASCENDING)])

    if regex:
        regex = re.compile(regex)

    # Put time/value series into result, using metrics_name as key
    result = defaultdict(list)
    for doc in docs:
        epoch_time = doc['epoch_time']

        for metrics in doc['metrics']:
            metrics_name = metrics['name']
            metrics_value = metrics['value']
            if regex:
                # Filter out unwanted metrics
                if regex.match(metrics_name):
                    result[metrics_name].append((epoch_time, metrics_value))
            else:
                result[metrics_name].append((epoch_time, metrics_value))

    return result


import bottle
bottle.debug(True)
#TODO: provide an app to work with wsgi server
run(host='localhost', port=9080, reloader=True)
