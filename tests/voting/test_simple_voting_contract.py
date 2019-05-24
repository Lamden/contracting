from unittest import TestCase
from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Datetime, Timedelta


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

    def test_timedelta_set_to_one_week_after_submission(self):
        day = Timedelta(days=1)
        week = Timedelta(weeks=1)

        self.assertEqual(self.simple_vote.election_interval.get(), week)
        self.assertEqual(self.simple_vote.voting_period.get(), day)

    def test_cant_vote_right_after_submission(self):
        with self.assertRaises(Exception):
            self.simple_vote.vote(v=5)

    def test_last_election_end_time_is_same_as_submission_time_after_submission(self):
        self.assertEqual(self.simple_vote.last_election_end_time.get(), Datetime(2019, 1, 1))

    def test_can_vote_one_week_after_submission(self):
        self.simple_vote.vote(v=5, environment={'now': Datetime(2019, 1, 10)})