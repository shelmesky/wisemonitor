from bottle import get, request, run
from pymongo import Connection, ASCENDING, DESCENDING

import conf


conn = Connection(conf.DB_HOST)
db = conn[conf.DB_NAME]


@get('/vm/<vm_name>')
def vm_metrics(vm_name):
    """Return VM metrics.

    TODO: docstring
    """

    query_params = {'name': vm_name}
    query_params.update(request.query)
    data = list(db.vm_metrics.find(query_params,
                                   ['epoch_time', 'metrics', 'cf', 'step'],
                                   sort=[('epoch_time', ASCENDING)]))
    return {'status': 'success', 'data': data}


import bottle
bottle.debug(True)
run(host='localhost', port=9080, reloader=True)
