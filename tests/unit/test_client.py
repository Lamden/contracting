from unittest import TestCase
from seneca.client import SenecaClient, AbstractContract
from seneca.ast.compiler import SenecaCompiler

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
        #self.c.raw_driver.flush()
        pass

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
            submission.submit_contract(name='tester', code=code)

            tester = self.c.get_contract('tester')

            self.assertEqual(tester.test(), 100)

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