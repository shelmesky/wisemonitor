from celery.task import task
import redis

from writer import write_metrics_pickle
from collector import collect_rrd_updates
from graphite_cli import GraphiteClient
from settings import REDIS


host, port, db = REDIS
r = redis.StrictRedis(host=host, port=port, db=db)


@task(ignore_result=True)
def xen_metrics_to_graphite(xenhosts, carbon_server, pickle_port):
    for host, username, password in xenhosts:
        one_xen_metrics_to_graphite.delay(host, username, password,
                                          carbon_server, pickle_port)


@task
def one_xen_metrics_to_graphite(xen_host_str, xen_username, xen_password,
                                carbon_server, pickle_port):
    """Send RRD from Xen host into Graphite/carbon."""
    key = 'xen:host:{0}:last_update'.format(xen_host_str)
    last_update = r.get(key)
    if last_update:
        start = int(last_update) + 1
    else:
        start = None

    updates = collect_rrd_updates(xen_host_str, xen_username, xen_password,
                                  start)
    cli = GraphiteClient(carbon_server, pickle_port=pickle_port)
    n_send = write_metrics_pickle(cli, updates.records)
    r.set(key, updates.end)

    return n_send
