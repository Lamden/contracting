from unittest import TestCase
from contracting.db.driver import ContractDriver
from contracting.execution.executor import Executor
from contracting.compilation.compiler import ContractingCompiler


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

        with open('../../contracting/contracts/submission.s.py') as f:
            contract = f.read()

        self.d.set_contract(name='submission',
                            code=contract,
                            author='sys')
        self.d.commit()

        self.compiler = ContractingCompiler()

    def tearDown(self):
        self.d.flush()

    def test_submission(self):
        e = Executor()

        code = '''@export
def d():
    a = 1
    return 1            
'''

        kwargs = {
            'name': 'stubucks',
            'code': code
        }

        e.execute(**TEST_SUBMISSION_KWARGS, kwargs=kwargs)

        new_code = self.compiler.parse_to_code(code)

        print(new_code)

        self.assertEqual(self.d.get_contract('stubucks'), new_code)

    def test_submission_then_function_call(self):
        e = Executor()

        code = '''@export
def d():
    return 1            
'''

        kwargs = {
            'name': 'stubucks',
            'code': code
        }

        e.execute(**TEST_SUBMISSION_KWARGS, kwargs=kwargs)
        status_code, result, _ = e.execute(sender='stu', contract_name='stubucks', function_name='d', kwargs={})

        self.assertEqual(result, 1)
        self.assertEqual(status_code, 0)

    def test_kwarg_helper(self):
        k = submission_kwargs_for_file('./test_contracts/test_orm_variable_contract.s.py')

        code = '''v = Variable()

@export
def set_v(i):
    v.set(i)

@export
def get_v():
    return v.get()
'''

        self.assertEqual(k['name'], 'test_orm_variable_contract')
        self.assertEqual(k['code'], code)

    def test_orm_variable_sets_in_contract(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/test_orm_variable_contract.s.py'))

        e.execute('stu', 'test_orm_variable_contract', 'set_v', kwargs={'i': 1000})

        i = self.d.get('test_orm_variable_contract.v')
        self.assertEqual(i, 1000)

    def test_orm_variable_gets_in_contract(self):
        e = Executor()

        print(e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/test_orm_variable_contract.s.py')))

        res = e.execute('stu', 'test_orm_variable_contract', 'get_v', kwargs={})

        self.assertEqual(res[1], None)

    def test_orm_variable_gets_and_sets_in_contract(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/test_orm_variable_contract.s.py'))

        e.execute('stu', 'test_orm_variable_contract', 'set_v', kwargs={'i': 1000})
        res = e.execute('stu', 'test_orm_variable_contract', 'get_v', kwargs={})

        self.assertEqual(res[1], 1000)

    def test_orm_hash_sets_in_contract(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/test_orm_hash_contract.s.py'))

        e.execute('stu', 'test_orm_hash_contract', 'set_h', kwargs={'k': 'key1', 'v': 1234})
        e.execute('stu', 'test_orm_hash_contract', 'set_h', kwargs={'k': 'another_key', 'v': 9999})

        key1 = self.d.get('test_orm_hash_contract.h:key1')
        another_key = self.d.get('test_orm_hash_contract.h:another_key')

        self.assertEqual(key1, 1234)
        self.assertEqual(another_key, 9999)

    def test_orm_hash_gets_in_contract(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/test_orm_hash_contract.s.py'))

        res = e.execute('stu', 'test_orm_hash_contract', 'get_h', kwargs={'k': 'test'})

        self.assertEqual(res[1], None)

    def test_orm_hash_gets_and_sets_in_contract(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/test_orm_hash_contract.s.py'))

        e.execute('stu', 'test_orm_hash_contract', 'set_h', kwargs={'k': 'key1', 'v': 1234})
        e.execute('stu', 'test_orm_hash_contract', 'set_h', kwargs={'k': 'another_key', 'v': 9999})

        _, key1, _ = e.execute('stu', 'test_orm_hash_contract', 'get_h', kwargs={'k': 'key1'})
        _, another_key, _ = e.execute('stu', 'test_orm_hash_contract', 'get_h', kwargs={'k': 'another_key'})

        self.assertEqual(key1, 1234)
        self.assertEqual(another_key, 9999)

    def test_orm_foreign_variable_sets_in_contract_doesnt_work(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/test_orm_variable_contract.s.py'))
        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/test_orm_foreign_key_contract.s.py'))

        e.execute('stu', 'test_orm_variable_contract', 'set_v', kwargs={'i': 1000})

        # this should fail
        status, _, _ = e.execute('stu', 'test_orm_foreign_key_contract', 'set_fv', kwargs={'i': 999})

        self.assertEqual(status, 1)

        _, i, _ = e.execute('stu', 'test_orm_variable_contract', 'get_v', kwargs={})
        self.assertEqual(i, 1000)

    def test_orm_foreign_variable_gets_in_contract(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/test_orm_variable_contract.s.py'))
        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/test_orm_foreign_key_contract.s.py'))

        e.execute('stu', 'test_orm_variable_contract', 'set_v', kwargs={'i': 424242})

        # this should fail
        _, i, _ = e.execute('stu', 'test_orm_foreign_key_contract', 'get_fv', kwargs={})

        self.assertEqual(i, 424242)

    def test_orm_foreign_hash_sets_in_contract_doesnt_work(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/test_orm_hash_contract.s.py'))
        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/test_orm_foreign_hash_contract.s.py'))

        e.execute('stu', 'test_orm_hash_contract', 'set_h', kwargs={'k': 'key1', 'v': 1234})
        e.execute('stu', 'test_orm_hash_contract', 'set_h', kwargs={'k': 'another_key', 'v': 9999})

        status_1, _, _ = e.execute('stu', 'test_orm_foreign_hash_contract', 'set_fh', kwargs={'k': 'key1', 'v': 5555})
        status_2, _, _ = e.execute('stu', 'test_orm_foreign_hash_contract', 'set_fh', kwargs={'k': 'another_key', 'v': 1000})

        key1 = self.d.get('test_orm_hash_contract.h:key1')
        another_key = self.d.get('test_orm_hash_contract.h:another_key')

        self.assertEqual(key1, 1234)
        self.assertEqual(another_key, 9999)
        self.assertEqual(status_1, 1)
        self.assertEqual(status_2, 1)

    def test_orm_foreign_hash_gets_and_sets_in_contract(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/test_orm_hash_contract.s.py'))

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/test_orm_foreign_hash_contract.s.py'))

        e.execute('stu', 'test_orm_hash_contract', 'set_h', kwargs={'k': 'key1', 'v': 1234})
        e.execute('stu', 'test_orm_hash_contract', 'set_h', kwargs={'k': 'another_key', 'v': 9999})

        _, key1, _ = e.execute('stu', 'test_orm_foreign_hash_contract', 'get_fh', kwargs={'k': 'key1'})
        _, another_key, _ = e.execute('stu', 'test_orm_foreign_hash_contract', 'get_fh', kwargs={'k': 'another_key'})

        self.assertEqual(key1, 1234)
        self.assertEqual(another_key, 9999)

    def test_orm_contract_not_accessible(self):
        e = Executor()

        res = e.execute(**TEST_SUBMISSION_KWARGS,
            kwargs=submission_kwargs_for_file('./test_contracts/test_orm_no_contract_access.s.py'))

        self.assertIsInstance(res[1], Exception)

    def test_construct_function_sets_properly(self):
        e = Executor()

        r = e.execute(**TEST_SUBMISSION_KWARGS,
            kwargs=submission_kwargs_for_file('./test_contracts/test_construct_function_works.s.py'))

        res = e.execute('stu', 'test_construct_function_works', 'get', kwargs={})

        self.assertEqual(res[1], 42)

    def test_import_exported_function_works(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                        kwargs=submission_kwargs_for_file('./test_contracts/import_this.s.py'))

        e.execute(**TEST_SUBMISSION_KWARGS,
                        kwargs=submission_kwargs_for_file('./test_contracts/importing_that.s.py'))

        res = e.execute('stu', 'importing_that', 'test', kwargs={})

        self.assertEqual(res[1], 12345 - 1000)

    def test_arbitrary_environment_passing_works_via_executor(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/i_use_env.s.py'))

        this_is_a_passed_in_variable = 555

        env = {'this_is_a_passed_in_variable': this_is_a_passed_in_variable}

        _, res, _ = e.execute('stu', 'i_use_env', 'env_var', kwargs={}, environment=env)

        self.assertEqual(res, this_is_a_passed_in_variable)

    def test_arbitrary_environment_passing_fails_if_not_passed_correctly(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/i_use_env.s.py'))

        this_is_a_passed_in_variable = 555

        env = {'this_is_another_passed_in_variable': this_is_a_passed_in_variable}

        status, res, _ = e.execute('stu', 'i_use_env', 'env_var', kwargs={}, environment=env)

        self.assertEqual(status, 1)
