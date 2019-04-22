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


class TestComplexContracts(TestCase):
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

    def test_token_constuction_works(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/token.s.py'))

        res = e.execute('stu', 'token', 'balance', kwargs={'account': 'colin'})

        self.assertEqual(res[1], 100)

        res = e.execute('stu', 'token', 'balance', kwargs={'account': 'stu'})

        self.assertEqual(res[1], 1000000)

        res = e.execute('stu', 'token', 'balance', kwargs={'account': 'raghu'})

        self.assertEqual(res[1], None)