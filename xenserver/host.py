"""Xen host that serves RRD data through HTTP.

Classes:

    XenHost
    XenRRDHost
"""

import urllib

import XenAPI


class XenHost(object):
    """Encapsulate operations on Xen host.

    Members:
        host - hostname or ipaddress of the Xen host
        url - Connection URL string
        follow_master - whether to follow master node in the pool

    Methods:
        login
        logout
        find_vm
    """

    def __init__(self, host, username=None, password=None, scheme='http',
                 follow_master=False):
        """Construct a XenHost.

        When used inside a 'with' statement, login and logout are automatic.

        :param host: host of Xen
        :type host: string
        :param username: login username
        :param password: login password
        :param scheme: protocol to use, default is http
        :param follow_master: whether to auto connect pool master when the
        host itself is not the pool master, using same username and password.
        Useful if you have a pool of xen servers with same credentials.
        :type follow_master: boolean
        """
        self.host = host
        self.username = username
        self.password = password
        self.scheme = scheme
        self.follow_master = follow_master

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.logout()

    @property
    def url(self):
        """URL connetion string"""
        return '{scheme}://{host}'.format(scheme=self.scheme, host=self.host)

    def login(self):
        """Login to Xen host."""
        try:
            self.session = XenAPI.Session(self.url)
            self.session.xenapi.login_with_password(self.username,
                                                    self.password)
        except XenAPI.Failure as err:
            if err.details[0] == 'HOST_IS_SLAVE' and self.follow_master:
                pool_master = err.details[1]
                self.session = XenAPI.Session('http://%s' % pool_master)
                self.session.xenapi.login_with_password(self.username,
                                                        self.password)
            else:
                raise

    def logout(self):
        """Logout Xen host."""
        self.session.xenapi.logout()

    def find_vm(self, exclude_control_domain=True, **kwargs):
        """Find VMs that meets criteria.

        :param exclude_control_domain: do not count control domain in, default
        is True
        :param kwargs: queries in keyword argument form, e.g.,
        name_label='My VM'
        :returns: an iterator of matching VMs
        """

        vms = self.session.xenapi.VM.get_all()
        for vm in vms:
            record = self.session.xenapi.VM.get_record(vm)
            if record["is_a_template"]:
                continue
            if exclude_control_domain and record["is_control_domain"]:
                continue

            if all(query in record and record[query] == value
                   for query, value in kwargs.iteritems()):
                yield record

    def find_one_vm(self, **kwargs):
        """Find one VM that meets criteria. Calls find_vm. """
        try:
            return next(self.find_vm(**kwargs))
        except StopIteration:
            return None


class XenRRDHost(XenHost):
    """Encapsulate RRD operations from Xen host."""

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
        scheme = self.scheme
        username = self.username
        password = self.password
        host = self.host

        # For RRD, we can direct visit and avoid logging in with XenAPI.Session
        url = '{scheme}://{username}:{password}@{host}/{rrd_type}{query}'.format(**locals())

        # Adapt from parse_rrd.py from XenServer website, which says "this is
        # better than urllib.urlopen() as it raises an Exception on http 401
        # 'Unauthorised' error rather than drop into interactive mode".
        sock = urllib.URLopener().open(url)
        rrd_xml = sock.read()
        sock.close()

        return rrd_xml
