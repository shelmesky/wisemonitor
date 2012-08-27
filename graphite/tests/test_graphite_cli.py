from unittest import TestCase

from ..graphite_cli import GraphiteClient


def now():
    import time
    return int(time.time())


class TestWritePlainText(TestCase):

    def setUp(self):
        self.cli = GraphiteClient('localhost',
                                  text_port=2003, pickle_port=2004)

    def test_send_plain_text(self):
        self.cli.send_text('test.text', 1.2, now())

    def test_send_with_time_defaults_to_now(self):
        self.cli.send_text('test.text', 3.4)

    def test_send_pickle(self):
        import random
        data = [('test.pickle.%d.%s' % (i, metrics), (now(), random.random()))
                for metrics in ('cpu', 'network', 'disk')
                for i in range(5)]
        self.cli.send_pickle(data)
