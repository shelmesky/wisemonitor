"""Xen host that serves RRD data through HTTP.

Classes:

    XenRRDHost
"""

import urllib


class XenRRDHost(object):
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password

    def fetch_rrd_updates(self, start, cf=None, interval=None, host=True):
        params = {}
        params['start'] = start
        if host:
            params['host'] = True

        query_params = '&'.join(['{0}={1}'.format(k, v)
                          for k, v in params.iteritems()])
        query = '?{0}'.format(query_params)
        return self._fetch_rrd(rrd_type='rrd_updates', query=query)

    def fetch_host_rrd(self):
        return self._fetch_rrd(rrd_type='host_rrd')

    def fetch_vm_rrd(self, uuid):
        return self._fetch_rrd(rrd_type='vm_rrd',
                               query='?uuid={0}'.format(uuid))

    def _fetch_rrd(self, rrd_type, query=''):
        scheme = 'http'  #FIXME: hardcoded
        username = self.username
        password = self.password
        host = self.host

        url = '{scheme}://{username}:{password}@{host}/{rrd_type}{query}'.format(**locals())

        # Adapt from parse_rrd.py from XenServer website, which says "this is
        # better than urllib.urlopen() as it raises an Exception on http 401
        # 'Unauthorised' error rather than drop into interactive mode".
        sock = urllib.URLopener().open(url)
        rrd_xml = sock.read()
        sock.close()

        return rrd_xml
