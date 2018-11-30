import sys, redis
from contextlib import contextmanager
from io import StringIO
from unittest import TestCase
from seneca.engine.interface import SenecaInterface
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

    def setUp(self):
        self.si = SenecaInterface(False, port=get_redis_port(), password=get_redis_password())
        try: v = self.si.r.get('market:stamps_to_tau')
        except: v = 1
        self.si.r.flushdb()
        self.si.r.set('market:stamps_to_tau', v)
        print('\n{}'.format('#' * 128))
        print(self.id)
        print('{}\n'.format('#' * 128))
