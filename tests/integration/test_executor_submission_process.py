from unittest import TestCase
from seneca.db.driver import ContractDriver
from seneca.execution.executor import Executor


def submission_kwargs_for_file(f):
    # Get the file name only by splitting off directories
    split = f.split('/')
    split = split[-1]

    # Now split off the .s
    split = split.split('.')
    contract_name = split[0]

    with open(f) as file:
        contract_code = file.read()

    return {
        'name': contract_name,
        'code': contract_code,
    }


TEST_SUBMISSION_KWARGS = {
    'sender': 'stu',
    'contract_name': 'submission',
    'function_name': 'submit_contract'
}


class TestExecutor(TestCase):
    def setUp(self):
        self.d = ContractDriver()
        self.d.flush()

        with open('../../seneca/contracts/submission.s.py') as f:
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

        e.execute(**TEST_SUBMISSION_KWARGS, kwargs=kwargs)

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

        e.execute(**TEST_SUBMISSION_KWARGS, kwargs=kwargs)
        status_code, result = e.execute(sender='stu', contract_name='stubucks', function_name='d', kwargs={})

        self.assertEqual(result, 1)
        self.assertEqual(status_code, 0)

    def test_kwarg_helper(self):
        k = submission_kwargs_for_file('./test_contracts/test_orm_variable_contract.s.py')

        code = '''v = Variable()

@seneca_export
def set_v(i):
    v.set(i)

@seneca_export
def get_v():
    return v.get()
'''

        self.assertEqual(k['name'], 'test_orm_variable_contract')
        self.assertEqual(k['code'], code)

    def test_orm_variable_sets_in_contract(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/test_orm_variable_contract.s.py'))

        res = e.execute('stu', 'test_orm_variable_contract', 'set_v', kwargs={'i': 1000})

        i = self.d.get('test_orm_variable_contract.v')
        self.assertEqual(i, 1000)

    def test_orm_variable_gets_in_contract(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/test_orm_variable_contract.s.py'))

        res = e.execute('stu', 'test_orm_variable_contract', 'get_v', kwargs={})

        self.assertEqual(res[1], None)

    def test_orm_variable_gets_and_sets_in_contract(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/test_orm_variable_contract.s.py'))

        e.execute('stu', 'test_orm_variable_contract', 'set_v', kwargs={'i': 1000})
        res = e.execute('stu', 'test_orm_variable_contract', 'get_v', kwargs={})

        self.assertEqual(res[1], 1000)
