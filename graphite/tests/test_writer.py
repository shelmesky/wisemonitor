from unittest import TestCase

from ..writer import write_metrics_pickle
from ..graphite_cli import GraphiteClient


def now():
    import time
    return int(time.time())


def rand():
    import random
    return random.randint(0, 100)


class TestWriteMetrics(TestCase):

    def setUp(self):
        self.carbon_server = 'localhost'
        self.text_port = 2003
        self.pickle_port = 2004

    def test_write_metrics_pickle_to_graphite(self):
        import os.path
        from ..xenrrd.parsers import RRDUpdates
        dir = os.path.dirname(__file__)
        with open(os.path.join(dir, 'test_xenrrd.data'), 'r') as f:
            records = RRDUpdates(f.read()).records
        cli = GraphiteClient(self.carbon_server)
        write_metrics_pickle(cli, None, records)
