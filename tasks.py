from celery.task import task

from importer import MongoDBImporter
from xenrrd.host import XenRRDHost


@task(ignore_result=True)
def import_rrd(db_host, db_name, xen_host_str, xen_username, xen_password):
    xen_rrd_host = XenRRDHost(xen_host_str, xen_username, xen_password)
    MongoDBImporter(db_host, db_name).import_rrd_updates(xen_rrd_host)

@task(ignore_result=True)
def import_all_rrd(db_host, db_name, xen_hosts):
    for (xen_host_str, xen_username, xen_password) in xen_hosts:
        import_rrd.delay(db_host, db_name,
                         xen_host_str, xen_username, xen_password)
