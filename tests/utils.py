from seneca.engine.interpreter.driver import Driver
from unittest import TestCase
from seneca.constants.config import get_redis_port, MASTER_DB, REDIS_PORT, get_redis_password
from seneca.engine.interpreter.executor import Executor
from seneca.tooling import *


class TestCaseHeader(TestCase):

    def setUp(self):
        print('\n{}'.format('#' * 128))
        print('\t', self.id)
        print('{}\n'.format('#' * 128))


class TestExecutor(TestCaseHeader):

    @classmethod
    def setUpClass(cls):
        cls.r = Driver(host='localhost', port=REDIS_PORT, db=MASTER_DB)
        cls.r.flushall()
        cls.reset()

    @classmethod
    def reset(cls, currency=False, concurrency=False):
        cls.r.flushall()
        cls.ex = Executor(currency=currency, concurrency=concurrency)

    @classmethod
    def flush(cls):
        cls.r.flushall()