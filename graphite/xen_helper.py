import redis

from settings import REDIS, XENSERVERS
from xenrrd.host import XenHost


host, port, db = REDIS
r = redis.StrictRedis(host=host, port=port, db=db)


def lookup_vm_name_by_uuid(uuid):
    key = 'xen:vm:uuid:{0}:vm_name'.format(uuid)
    vm_name = r.get(key)

    if vm_name:
        return vm_name

    for host, username, password in XENSERVERS:
        with XenHost(host, username, password, follow_master=True) as xen_host:
            vm = xen_host.find_one_vm(uuid=uuid,
                                      exclude_control_domain=False)
            if vm is not None:
                vm_name = vm.get('name_label')
                r.set(key, vm_name)  # cache it
                return vm_name
    raise LookupError('Cannot find name for uuid {0}.'.format(uuid))
