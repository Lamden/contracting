from unittest import TestCase
from seneca.client import SenecaClient, AbstractContract

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

        self.assertEqual(self.c.raw_driver.get_contract('test'), code)

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
