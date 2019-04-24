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
        self.d.commit()

    def tearDown(self):
        self.d.flush()

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

    def test_erc20_clone_construction_works(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/erc20_clone.s.py'))

        _, stu = e.execute('stu', 'erc20_clone', 'balance_of', kwargs={'account': 'stu'})
        _, colin = e.execute('stu', 'erc20_clone', 'balance_of', kwargs={'account': 'colin'})
        _, supply = e.execute('stu', 'erc20_clone', 'total_supply', kwargs={})

        self.assertEqual(stu, 1000000)
        self.assertEqual(colin, 100)
        self.assertEqual(supply, 1000100)

    def test_erc20_clone_transfer_works(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/erc20_clone.s.py'))

        e.execute('stu', 'erc20_clone', 'transfer', kwargs={'amount': 1000000, 'to': 'raghu'})
        _, raghu = e.execute('stu', 'erc20_clone', 'balance_of', kwargs={'account': 'raghu'})
        _, stu = e.execute('stu', 'erc20_clone', 'balance_of', kwargs={'account': 'stu'})

        self.assertEqual(raghu, 1000000)
        self.assertEqual(stu, 0)

    def test_erc20_clone_transfer_fails(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/erc20_clone.s.py'))

        status, res = e.execute('stu', 'erc20_clone', 'transfer', kwargs={'amount': 10000000, 'to': 'raghu'})

        self.assertEqual(status, 1)
        self.assertEqual(type(res), AssertionError)

    def test_allowance_of_blank(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/erc20_clone.s.py'))

        status, res = e.execute('stu', 'erc20_clone', 'allowance', kwargs={'owner': 'stu', 'spender': 'raghu'})
        self.assertEqual(res, 0)

    def test_approve_works_and_allowance_shows(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/erc20_clone.s.py'))

        e.execute('stu', 'erc20_clone', 'approve', kwargs={'amount': 1234, 'to': 'raghu'})

        status, res = e.execute('stu', 'erc20_clone', 'allowance', kwargs={'owner': 'stu', 'spender': 'raghu'})
        self.assertEqual(res, 1234)

    def test_approve_and_transfer_from(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/erc20_clone.s.py'))

        e.execute('stu', 'erc20_clone', 'approve', kwargs={'amount': 1234, 'to': 'raghu'})
        e.execute('raghu', 'erc20_clone', 'transfer_from', kwargs={'amount': 123, 'to': 'tejas', 'main_account': 'stu'})
        _, raghu = e.execute('stu', 'erc20_clone', 'balance_of', kwargs={'account': 'raghu'})
        _, stu = e.execute('stu', 'erc20_clone', 'balance_of', kwargs={'account': 'stu'})
        _, tejas = e.execute('stu', 'erc20_clone', 'balance_of', kwargs={'account': 'tejas'})

        self.assertEqual(raghu, 0)
        self.assertEqual(stu, (1000000 - 123))
        self.assertEqual(tejas, 123)

    def test_failure_after_data_writes_doesnt_commit(self):
        e = Executor()

        e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/leaky.s.py'))

        e.execute('colin', 'leaky', 'transfer', kwargs={'amount': 1234, 'to': 'raghu'})

        _, raghu = e.execute('stu', 'leaky', 'balance_of', kwargs={'account': 'raghu'})
        _, colin = e.execute('stu', 'leaky', 'balance_of', kwargs={'account': 'colin'})

        self.assertEqual(raghu, 0)
        self.assertEqual(colin, 100)

    def test_leaky_contract_commits_on_success(self):
        e.execute('colin', 'leaky', 'transfer', kwargs={'amount': 1, 'to': 'raghu'})

        _, raghu = e.execute('stu', 'leaky', 'balance_of', kwargs={'account': 'raghu'})
        _, colin = e.execute('stu', 'leaky', 'balance_of', kwargs={'account': 'colin'})

        self.assertEqual(raghu, 1)
        self.assertEqual(colin, 99)