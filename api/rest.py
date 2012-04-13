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


import bottle
bottle.debug(True)
run(host='localhost', port=9080, reloader=True)
