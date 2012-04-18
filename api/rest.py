from collections import defaultdict

from bottle import get, request, run
from pymongo import Connection, ASCENDING

import conf


conn = Connection(conf.DB_HOST)
db = conn[conf.DB_NAME]


@get('/vm/<vm_name>/')
def vm_metrics(vm_name):
    """Return all metrics of the specified VM.

    Supported query parameters:
        start - start time of data points in seconds since epoch
        end - start time of data points in seconds since epoch

    Example:
        http://localhost/vm/i-4-33-VM/?start=1334280890&end=1334280910
    """

    query_params = {'name': vm_name}
    time_range = defaultdict(dict)
    if request.query.start:
        time_range['$gte'] = int(request.query.start)
    if request.query.end:
        time_range['$lte'] = int(request.query.end)
    if time_range:
        query_params['epoch_time'] = time_range
    data = list(db.vm_metrics.find(query_params,
                                   ['epoch_time', 'metrics', 'cf', 'step'],
                                   sort=[('epoch_time', ASCENDING)]))
    return {'status': 'success', 'data': data}


@get('/vm/<vm_name>/cpu/')
def cpu_metrics(vm_name):
    """Return CPU metrics of the specified VM.

    Supported query parameters:
        start - start time of data points in seconds since epoch
        end - start time of data points in seconds since epoch

    Example:
        http://localhost/vm/i-4-33-VM/cpu/?start=1334280890&end=1334280910
    """

    result = query_helper(vm_name, request.query, '^cpu')

    return {'status': 'success', 'result': result}


@get('/vm/<vm_name>/vif/')
def vif_metrics(vm_name):
    """
    TODO: docstring
    """
    result = query_helper(vm_name, request.query, '^vif_')

    return {'status': 'success', 'result': result}


def query_helper(vm_name, query, regex=None):
    query_params = {'name': vm_name}

    if regex:
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
    data = db.vm_metrics.find(query_params,
                              ['epoch_time', 'metrics'],
                              sort=[('epoch_time', ASCENDING)])

    import re
    if regex:
        regex = re.compile(regex)

    result = defaultdict(list)
    for record in data:
        epoch_time = record['epoch_time']
        for i in record['metrics']:
            metrics_name = i['name']
            value = i['value']
            if regex:
                if regex.match(metrics_name):
                    result[metrics_name].append((epoch_time, value))
            else:
                result[metrics_name].append((epoch_time, value))

    return result


import bottle
bottle.debug(True)
run(host='localhost', port=9080, reloader=True)
