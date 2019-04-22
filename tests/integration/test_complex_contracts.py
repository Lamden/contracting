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
                  kwargs=submission_kwargs_for_file('./test_contracts/currency.s.py'))

        res = e.execute('stu', 'currency', 'balance', kwargs={'account': 'colin'})
        self.assertEqual(res[1], 100)

        res = e.execute('stu', 'currency', 'balance', kwargs={'account': 'stu'})
        self.assertEqual(res[1], 1000000)

        res = e.execute('stu', 'currency', 'balance', kwargs={'account': 'raghu'})
        self.assertEqual(res[1], None)

    def test_token_transfer_works(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/currency.s.py'))

        e.execute('stu', 'currency', 'transfer', kwargs={'amount': 1000, 'to': 'colin'})

        _, stu_balance = e.execute('stu', 'currency', 'balance', kwargs={'account': 'stu'})
        _, colin_balance = e.execute('stu', 'currency', 'balance', kwargs={'account': 'colin'})

        self.assertEqual(stu_balance, 1000000 - 1000)
        self.assertEqual(colin_balance, 100 + 1000)

    def test_token_transfer_failure_not_enough_to_send(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/currency.s.py'))

        status, res = e.execute('stu', 'currency', 'transfer', kwargs={'amount': 1000001, 'to': 'colin'})

        self.assertEqual(status, 1)

    def test_token_transfer_to_new_account(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/currency.s.py'))

        e.execute('stu', 'currency', 'transfer', kwargs={'amount': 1000, 'to': 'raghu'})

        _, raghu_balance = e.execute('stu', 'currency', 'balance', kwargs={'account': 'raghu'})

        self.assertEqual(raghu_balance, 1000)