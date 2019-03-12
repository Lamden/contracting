from seneca.engine.interpreter.driver import Driver
from unittest import TestCase
from seneca.constants.config import MASTER_DB, LEDIS_PORT
from seneca.engine.interpreter.executor import Executor
from seneca.engine.interpreter.parser import Parser
from seneca.libs.storage.table import Table
import ledis, pickle


class TestCaseHeader(TestCase):

    def setUp(self):
        print('\n{}'.format('#' * 128))
        print('\t', self.id)
        print('{}\n'.format('#' * 128))


class TestExecutor(TestCaseHeader):

    @classmethod
    def setUpClass(cls):
        cls.r = Driver(host='localhost', port=LEDIS_PORT, db=MASTER_DB)
        cls.r.flushall()
        cls.reset()

    @classmethod
    def reset(cls, currency=False, concurrency=False):
        cls.r.flushall()
        cls.ex = Executor(currency=currency, concurrency=concurrency)

    @classmethod
    def flush(cls):
        cls.r.flushall()
    #
    # @classmethod
    # def tearDownClass(cls):
    #     Parser.initialized = False


class MockExecutor:
    def __init__(self, *args, **kwargs):
        self.driver = ledis.Ledis(host='localhost', port=LEDIS_PORT, db=MASTER_DB)
        self.driver.flushall()
        Parser.executor = self
        if not Parser.parser_scope.get('rt'):
            Parser.parser_scope['rt'] = {}
        Parser.parser_scope['rt'].update({
            'contract': 'sample',
            'sender': 'falcon',
            'author': '__lamden_io__'
        })


class TestDataTypes(TestCaseHeader):

    def setUp(self):
        self.contract_id = self.id().split('.')[-1]
        self.ex = MockExecutor()
        Parser.parser_scope['rt']['contract'] = self.contract_id
        Table.schemas = {}
        super().setUp()
