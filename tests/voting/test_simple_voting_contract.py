from unittest import TestCase
from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Datetime


class TestSenecaClientReplacesExecutor(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu', environment={'now': Datetime(2019, 1, 1)})
        self.c.raw_driver.flush()

        with open('../../contracting/contracts/submission.s.py') as f:
            contract = f.read()

        self.c.raw_driver.set_contract(name='submission', code=contract, author='sys')

        self.c.raw_driver.commit()

        submission = self.c.get_contract('submission')

        # submit erc20 clone
        with open('./contracts/simple_vote.s.py') as f:
            code = f.read()
            submission.submit_contract(name='simple_vote', code=code, environment={'now': Datetime(2019, 1, 1)})

        self.simple_vote = self.c.get_contract('simple_vote')

    def tearDown(self):
        #self.c.raw_driver.flush()
        pass

    def test_votable_is_100_after_submission(self):
        self.assertEqual(self.simple_vote.votable.get(), 100)

    def test_in_election_is_false_after_submission(self):
        self.assertEqual(self.simple_vote.in_election.get(), False)