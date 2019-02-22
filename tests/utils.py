import sys, redis
from contextlib import contextmanager
from io import StringIO
from unittest import TestCase
from seneca.engine.interface import SenecaInterface
from seneca.constants.config import get_redis_port, MASTER_DB, REDIS_PORT, get_redis_password
from seneca.engine.interpret.executor import Executor


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
        self.si.r.flushall()
        print('\n{}'.format('#' * 128))
        print(self.id)
        print('{}\n'.format('#' * 128))

class TestExecutor(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.r = redis.StrictRedis(host='localhost', port=REDIS_PORT, db=MASTER_DB)
        cls.reset()

    def setUp(self):
        print('\n{}'.format('#' * 128))
        print(self.id)
        print('{}\n'.format('#' * 128))

    @classmethod
    def reset(cls, currency=False, concurrency=False):
        cls.r.flushall()
        cls.ex = Executor(currency=currency, concurrency=concurrency)

    @classmethod
    def flush(cls):
        cls.r.flushall()