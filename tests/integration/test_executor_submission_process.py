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

        kwargs = {
            'name': 'stubucks',
            'code': '''
@seneca_export
def d():
    print('yup')            
'''
        }

        status = e.execute(sender='stu', contract_name='submission', function_name='submit_contract', kwargs=kwargs)

        print(status)

        print(self.d.get_contract('stubucks'))
        print(self.d.get_contract('submission'))