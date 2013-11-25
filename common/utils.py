#!/usr/bin/python
import sys
import time
from datetime import datetime, timedelta
import settings
import copy
import httplib
import xmlrpclib


def time_stamp_to_string(time_stamp, f=None):
    if not isinstance(time_stamp, float) \
            and not isinstance(time_stamp, int):
        try:
            time_stamp = float(time_stamp)
        except Exception:
            raise RuntimeError("Need float or int or string arugument.")
    if not f:
        f = '%Y-%m-%d %H:%M:%S'
    return time.strftime(f, time.localtime(time_stamp))


class TimeoutTransport(xmlrpclib.Transport):
    timeout = settings.XENSERVER_CONNECT_TIMEOUT
    def set_timeout(self, timeout):
        self.timeout = timeout
    
    def make_connection(self, host):
        return httplib.HTTPConnection(host, timeout=self.timeout)


def force_print(msg):
    print >> sys.stderr, msg


def make_timestamp(datetime):
    return int(time.mktime(datetime))


def get_before(**kwargs):
    now = datetime.now()
    return now - timedelta(**kwargs)


def get_four_hours_ago():
    ago = get_before(seconds=14400)
    return make_timestamp(ago.timetuple())


def get_one_day_ago():
    ago = get_before(days=1)
    return make_timestamp(ago.timetuple())


def get_one_week_ago():
    ago = get_before(days=30)
    return make_timestamp(ago.timetuple())


def get_one_year_ago():
    ago = get_before(days=365)
    return make_timestamp(ago.timetuple())


def get_chart_colors():
    original_colors = settings.CHART_COLORS
    colors = copy.deepcopy(original_colors)
    colors.reverse()
    return colors


if __name__ == '__main__':
    print get_four_hours_ago()
    print get_one_day_ago()
    print get_one_week_ago()
    print get_one_year_ago()
    