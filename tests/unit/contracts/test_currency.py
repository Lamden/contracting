from tests.utils import TestExecutor
import seneca
from os.path import join, dirname

PATH = seneca.__path__[0] + '/../test_contracts/'
AUTHOR = '__lamden_io__'


class TestCurrency(TestExecutor):

    def setUp(self):
        super().setUp()
        with open(join(PATH, 'new_currency.sen.py')) as f:
            self.ex.execute_function('smart_contract', 'submit_contract', AUTHOR, kwargs={
                'contract_name': 'new_currency',
                'code_str': f.read()
            })

    def test_class(self):
        pass