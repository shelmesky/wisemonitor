from unittest import TestCase

from ..collector import collect_rrd_updates


class TestCollector(TestCase):

    def test_against_real_xenserver(self):
        it = collect_rrd_updates('192.2.3.215', 'rrd', '123456')
        it = collect_rrd_updates('192.2.3.216', 'rrd', '123456')
