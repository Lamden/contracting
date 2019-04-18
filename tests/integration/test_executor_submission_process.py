from unittest import TestCase
from seneca.db.driver import ContractDriver
from seneca.execution.executor import Executor


class TestExecutor(TestCase):
    def setUp(self):
        self.d = ContractDriver()
        self.d.flush()

        with open('../../seneca/contracts/genesis/submission.s.py') as f:
            contract = f.read()

        self.d.set_contract(name='submission',
                            code=contract,
                            author='sys')

    def tearDown(self):
        #self.d.flush()
        pass

    def test_submission(self):
        e = Executor()

        code = '''@seneca_export
def d():
    return 1            
'''

        kwargs = {
            'name': 'stubucks',
            'code': code
        }

        e.execute(sender='stu', contract_name='submission', function_name='submit_contract', kwargs=kwargs)

        self.assertEqual(self.d.get_contract('stubucks'), code)

    def test_submission_then_function_call(self):
        e = Executor()

        code = '''@seneca_export
def d():
    return 1            
'''

        kwargs = {
            'name': 'stubucks',
            'code': code
        }

        e.execute(sender='stu', contract_name='submission', function_name='submit_contract', kwargs=kwargs)
        status_code, result = e.execute(sender='stu', contract_name='stubucks', function_name='d', kwargs={})

        self.assertEqual(result, 1)
        self.assertEqual(status_code, 0)