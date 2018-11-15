import sys, redis
from contextlib import contextmanager
from io import StringIO
from unittest import TestCase
from seneca.engine.interface import SenecaInterface
from seneca.engine.interpreter import SenecaInterpreter
from seneca.constants.config import get_redis_port, MASTER_DB, DB_OFFSET, get_redis_password

def recur_fibo(n):
    if n <= 1:
        return n
    else:
        return(recur_fibo(n-1) + recur_fibo(n-2))

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
        self.si = SenecaInterface(False)
        SenecaInterpreter.setup(False)
        print('\n{}'.format('#' * 128))
        print(self.id)
        print('{}\n'.format('#' * 128))

    @classmethod
    def tearDownClass(cls):
        cls.r.flushdb()
