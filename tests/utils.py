import sys, redis
from contextlib import contextmanager
from io import StringIO
from unittest import TestCase
from seneca.interface.interface import SenecaInterface
from seneca.engine.interpreter import SenecaInterpreter

@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err

class TestInterface(TestCase):
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    def setUp(self):
        self.r.flushdb()
        # Only do this once in each process!
        SenecaInterpreter.setup()
        self.si = SenecaInterface()
        print('''
################################################################################
{}
################################################################################
        '''.format(self.id))
