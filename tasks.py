from celery.task import task
from redis import Redis

from importer import MongoDBImporter
from xenrrd.host import XenRRDHost


@task
def import_rrd(db_host, db_name, redis_host, redis_db,
               xen_host_str, xen_username, xen_password):
    """Import RRD from Xen host into MongoDB.

    Return number of records imported.
    Don't import if a previous same task is running.
    """

    # Lock if a previous task importing from same Xen host is running.
    # Adapted from http://loose-bits.com/2010/10/distributed-task-locking-in-celery.html
    have_lock = False
    r = Redis(host=redis_host, db=redis_db)
    lock = r.lock('import-rrd-from-{0}'.format(xen_host_str))
    try:
        have_lock = lock.acquire(blocking=False)
        if have_lock:
            xen_rrd_host = XenRRDHost(xen_host_str, xen_username, xen_password)
            return MongoDBImporter(db_host, db_name).import_rrd_updates(xen_rrd_host)
        else:
            return 0
    finally:
        if have_lock:
            lock.release()


@task
def import_all_rrd(db_host, db_name, redis_host, redis_db, xen_hosts):
    results = [import_rrd.delay(db_host, db_name, redis_host, redis_db,
                                xen_host_str, xen_username, xen_password)
               for (xen_host_str, xen_username, xen_password) in xen_hosts]
    return sum(result.get() for result in results)
