import sys, redis
from contextlib import contextmanager
from io import StringIO
from unittest import TestCase
from seneca.engine.interface import SenecaInterface
from seneca.engine.interpreter import SenecaInterpreter
from seneca.constants.redis_config import get_redis_port, MASTER_DB, DB_OFFSET, get_redis_password

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
    r = redis.StrictRedis(host='localhost', port=get_redis_port(), db=MASTER_DB, password=get_redis_password())
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
