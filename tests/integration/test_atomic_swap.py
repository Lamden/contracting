from unittest import TestCase
from seneca.db.driver import ContractDriver
from seneca.execution.executor import Executor
from seneca.stdlib.bridge.time import Datetime

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


class TestAtomicSwapContract(TestCase):
    def setUp(self):
        self.d = ContractDriver()
        self.d.flush()

        with open('../../seneca/contracts/submission.s.py') as f:
            contract = f.read()

        self.d.set_contract(name='submission',
                            code=contract,
                            author='sys')
        self.d.commit()

        self.e = Executor()

        print(self.e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/erc20_clone.s.py')))

        self.e.execute(**TEST_SUBMISSION_KWARGS,
                  kwargs=submission_kwargs_for_file('./test_contracts/atomic_swaps.s.py'))

    def tearDown(self):
        #self.d.flush()
        pass

    def test_initiate_not_enough_approved(self):
        self.e.execute('stu', 'erc20_clone', 'approve', kwargs={'amount': 1000000, 'to': 'atomic_swaps'})
        status, res = self.e.execute('stu', 'atomic_swaps', 'initiate', kwargs={
            'participant': 'raghu',
            'expiration': Datetime(2020, 1, 1),
            'hashlock': '6c839446b4d4fa2582af5011730c680b3ee39929f041b7bee6f376211cc710f7',
            'amount': 5000000
        })

        self.assertEqual(status, 1)
        self.assertTrue(isinstance(res, AssertionError))

    def test_initiate_transfers_coins_correctly(self):
        self.e.execute('stu', 'erc20_clone', 'approve', kwargs={'amount': 1000000, 'to': 'atomic_swaps'})
        self.e.execute('stu', 'atomic_swaps', 'initiate', kwargs={
            'participant': 'raghu',
            'expiration': Datetime(2020, 1, 1),
            'hashlock': '6c839446b4d4fa2582af5011730c680b3ee39929f041b7bee6f376211cc710f7',
            'amount': 5
        })

        _, atomic_swaps = self.e.execute('stu', 'erc20_clone', 'balance_of', kwargs={'account':'atomic_swaps'})
        _, stu = self.e.execute('stu', 'erc20_clone', 'balance_of', kwargs={'account': 'stu'})
        _, stu_as = self.e.execute('stu', 'erc20_clone', 'allowance', kwargs={'owner': 'stu', 'spender': 'atomic_swaps'})

        self.assertEqual(atomic_swaps, 5)
        self.assertEqual(stu, 999995)
        self.assertEqual(stu_as, 999995)

    def test_initiate_writes_to_correct_key_and_properly(self):
        self.e.execute('stu', 'erc20_clone', 'approve', kwargs={'amount': 1000000, 'to': 'atomic_swaps'})
        self.e.execute('stu', 'atomic_swaps', 'initiate', kwargs={
            'participant': 'raghu',
            'expiration': Datetime(2020, 1, 1),
            'hashlock': '6c839446b4d4fa2582af5011730c680b3ee39929f041b7bee6f376211cc710f7',
            'amount': 5
        })

        key = 'atomic_swaps.swaps:raghu:6c839446b4d4fa2582af5011730c680b3ee39929f041b7bee6f376211cc710f7'

        expiration, amount = self.d.get(key)
        self.assertEqual(expiration, Datetime(2020, 1, 1))
        self.assertEqual(amount, 5)

    def test_redeem_on_wrong_secret_fails(self):
        self.e.execute('stu', 'erc20_clone', 'approve', kwargs={'amount': 1000000, 'to': 'atomic_swaps'})
        self.e.execute('stu', 'atomic_swaps', 'initiate', kwargs={
            'participant': 'raghu',
            'expiration': Datetime(2020, 1, 1),
            'hashlock': '6c839446b4d4fa2582af5011730c680b3ee39929f041b7bee6f376211cc710f7',
            'amount': 5
        })

        s, r = self.e.execute('raghu', 'atomic_swaps', 'redeem', kwargs={'secret': '00'})

        self.assertEqual(s, 1)
        self.assertEqual(str(r), 'Incorrect sender or secret passed.')


    def test_redeem_on_wrong_sender_fails(self):
        self.e.execute('stu', 'erc20_clone', 'approve', kwargs={'amount': 1000000, 'to': 'atomic_swaps'})
        self.e.execute('stu', 'atomic_swaps', 'initiate', kwargs={
            'participant': 'raghu',
            'expiration': Datetime(2020, 1, 1),
            'hashlock': '6c839446b4d4fa2582af5011730c680b3ee39929f041b7bee6f376211cc710f7',
            'amount': 5
        })

        s, r = self.e.execute('stu', 'atomic_swaps', 'redeem', kwargs={'secret': '1a54390942257a70bb843c1bd94eb996'})

        self.assertEqual(s, 1)
        self.assertEqual(str(r), 'Incorrect sender or secret passed.')