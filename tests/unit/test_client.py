from unittest import TestCase
from seneca.client import SenecaClient, AbstractContract
from seneca.ast.compiler import SenecaCompiler
from seneca.db.orm import Variable, Hash


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


class TestSenecaClient(TestCase):
    def setUp(self):
        self.c = SenecaClient()
        self.c.raw_driver.flush()

        with open('../../seneca/contracts/submission.s.py') as f:
            contract = f.read()

        self.c.raw_driver.set_contract(name='submission',
                            code=contract,
                            author='sys')

        self.c.raw_driver.commit()

    def tearDown(self):
        self.c.raw_driver.flush()

    def test_get_contract_returns_correct_type(self):
        submission = self.c.get_contract('submission')
        self.assertTrue(isinstance(submission, AbstractContract))

    def test_get_contract_returns_contract_with_correct_functions(self):
        submission = self.c.get_contract('submission')
        self.assertIn('submit_contract', dir(submission))

    def test_get_contract_inits_mirror_clients(self):
        submission = self.c.get_contract('submission')
        self.assertEqual(self.c.executor, submission.executor)
        self.assertEqual(self.c.signer, submission.signer)

    def test_abstract_function_fails_without_proper_kwargs(self):
        submission = self.c.get_contract('submission')
        with self.assertRaises(AssertionError):
            submission.submit_contract()

    def test_abstract_function_fails_without_kwargs_not_none(self):
        submission = self.c.get_contract('submission')
        with self.assertRaises(AssertionError):
            submission.submit_contract(name=None, code=None)

    def test_abstract_function_fails_without_both_kwargs_none(self):
        submission = self.c.get_contract('submission')
        with self.assertRaises(AssertionError):
            submission.submit_contract(name=None, code='')

    def test_abstract_function_succeeds_and_publishes_contract(self):
        submission = self.c.get_contract('submission')
        code = '''
@seneca_export
def test():
    return 100
        '''

        submission.submit_contract(name='test', code=code)

        compiler = SenecaCompiler()
        new_code = compiler.parse_to_code(code)

        self.assertEqual(self.c.raw_driver.get_contract('test'), new_code)

    def test_abstract_function_succeeds_and_new_contract_can_be_abstracted(self):
            submission = self.c.get_contract('submission')
            code = '''
@seneca_export
def test():
    return 100
            '''
            submission.submit_contract(name='testy', code=code)

            tester = self.c.get_contract('testy')

            self.assertEqual(tester.test(), 100)

    def test_abstract_function_fails_and_raises_error(self):
        submission = self.c.get_contract('submission')
        code = '''
@seneca_export
def test(x):
    assert x == 7, "X is not seven!"
'''

        submission.submit_contract(name='tester', code=code)

        tester = self.c.get_contract('tester')

        with self.assertRaises(AssertionError):
            tester.test(x=100)

    def test_closure_to_code_string(self):
        def howdy():
            @seneca_export
            def sup():
                return 5

        code_string, name = self.c.closure_to_code_string(howdy)
        code = '''@seneca_export
def sup():
    return 5
'''

        self.assertEqual(code_string, code)
        self.assertEqual(name, 'howdy')

    def test_lint_string_no_violations(self):
        code = '''
@seneca_export
def test():
    return 100
'''
        violations = self.c.lint(code)
        self.assertIsNone(violations)

    def test_lint_closure_no_violations(self):
        def howdy():
            @seneca_export
            def test():
                return 100

        violations = self.c.lint(howdy)

        self.assertIsNone(violations)

    def test_lint_string_no_exports(self):
        code = '''
def test():
    return 100
'''
        violations = self.c.lint(code)
        self.assertEqual(violations[0], 'Line 0: S13- No valid seneca decorator found')

    def test_lint_closure_no_exports(self):
        def howdy():
            def test():
                return 100

        violations = self.c.lint(howdy)
        self.assertEqual(violations[0], 'Line 0: S13- No valid seneca decorator found')

    def test_lint_string_no_export_raises(self):
        code = '''
def test():
    return 100
'''
        with self.assertRaises(Exception):
            self.c.lint(code, raise_errors=True)

    def test_lint_closure_no_export_raises(self):
        def howdy():
            def test():
                return 100

        with self.assertRaises(Exception):
            self.c.lint(howdy, raise_errors=True)

    def test_compile_string(self):
        code = '''
@seneca_export
def test():
    return 100
'''

        compiled_code = self.c.compile(code)
        expected_code = self.c.compiler.parse_to_code(code)

        self.assertEqual(compiled_code, expected_code)

    def test_compile_closure(self):
        def howdy():
            @seneca_export
            def test():
                return 100

        code = '''
@seneca_export
def test():
    return 100
'''

        compiled_code = self.c.compile(howdy)
        expected_code = self.c.compiler.parse_to_code(code)

        self.assertEqual(compiled_code, expected_code)

    def test_submit_closure_works(self):
        def howdy():
            v = Variable()
            @seneca_export
            def test():
                return v.get()

        self.c.submit(howdy)
        howdy_con = self.c.get_contract('howdy')
        self.assertTrue(isinstance(howdy_con, AbstractContract))
        self.assertTrue(getattr(howdy_con, 'test'))

    def test_submit_string_works(self):
        code = '''v = Variable()
@seneca_export
def test():
    return v.get()'''

        self.c.submit(code, name='howdy')
        howdy_con = self.c.get_contract('howdy')
        self.assertTrue(isinstance(howdy_con, AbstractContract))
        self.assertTrue(getattr(howdy_con, 'test'))

    def test_submit_fails_on_no_name(self):
        code = '''v = Variable()
@seneca_export
def test():
    return v.get()'''

        with self.assertRaises(AssertionError):
            self.c.submit(code)

    def test_submit_fails_on_violations(self):
        code = '''v = Variable()
def test():
    return v.get()'''

        with self.assertRaises(Exception):
            self.c.submit(code, 'howdy')

    def test_get_variable_that_exists(self):
        def howdy():
            v = Variable()
            @seneca_export
            def test():
                return v.get()

            @seneca_construct
            def seed():
                v.set(1000)

        self.c.submit(howdy)

        howdy = self.c.get_contract('howdy')
        self.assertEqual(howdy.v.get(), 1000)
        self.assertTrue(isinstance(howdy.v, Variable))

    def test_get_variable_that_exists_sets_on_db(self):
        def howdy():
            v = Variable()
            @seneca_export
            def test():
                return v.get()

            @seneca_construct
            def seed():
                v.set(1000)

        self.c.submit(howdy)

        howdy = self.c.get_contract('howdy')
        howdy.v.set(1234)
        self.assertEqual(howdy.v.get(), 1234)
        self.assertTrue(isinstance(howdy.v, Variable))

    def test_get_variable_that_doesnt_exist_throws_attribute_error(self):
        def howdy():
            v = Variable()
            @seneca_export
            def test():
                return v.get()

            @seneca_construct
            def seed():
                v.set(1000)

        self.c.submit(howdy)

        howdy = self.c.get_contract('howdy')

        with self.assertRaises(AttributeError):
            howdy.x

    def test_get_protected_variable_that_exists_and_returns_string(self):
        def howdy():
            v = Variable()
            @seneca_export
            def test():
                return v.get()

            @seneca_construct
            def seed():
                v.set(1000)

        self.c.submit(howdy)

        howdy = self.c.get_contract('howdy')
        self.assertEqual(howdy.__author__, 'sys')

    def test_get_hash_returns_properly(self):
        def howdy():
            h = Hash()
            @seneca_export
            def test(f):
                return h[f]

            @seneca_construct
            def seed():
                h['stu'] = 'hello'

        self.c.submit(howdy)

        howdy = self.c.get_contract('howdy')

        self.assertEqual(howdy.h['stu'], 'hello')

    def test_get_hash_allows_setting_on_new_keys(self):
        def howdy():
            h = Hash()
            @seneca_export
            def test(f):
                return h[f]

            @seneca_construct
            def seed():
                h['stu'] = 'hello'

        self.c.submit(howdy)

        howdy = self.c.get_contract('howdy')

        howdy.h['yo'] = 123

        self.assertEqual(howdy.h['yo'], 123)

    def test_get_hash_allows_setting_which_overrides(self):
        def howdy():
            h = Hash()
            @seneca_export
            def test(f):
                return h[f]

            @seneca_construct
            def seed():
                h['stu'] = 'hello'

        self.c.submit(howdy)

        howdy = self.c.get_contract('howdy')

        howdy.h['stu'] = 123

        self.assertEqual(howdy.h['stu'], 123)

    def test_get_contracts(self):
        code = '''v = Variable()
@seneca_export
def test():
    return v.get()'''

        self.c.submit(code, name='howdy1')
        self.c.submit(code, name='howdy2')
        self.c.submit(code, name='howdy3')
        self.c.submit(code, name='howdy4')
        self.c.submit(code, name='howdy5')
        self.c.submit(code, name='howdy6')
        self.c.submit(code, name='howdy7')
        self.c.submit(code, name='howdy8')
        self.c.submit(code, name='howdy9')

        contracts = ['howdy1', 'howdy2', 'howdy3', 'howdy4',
                     'howdy5', 'howdy6', 'howdy7', 'howdy8',
                     'howdy9', 'submission', ]

        self.assertListEqual(contracts, self.c.get_contracts())
        print(self.c.get_contracts())