from unittest import TestCase
from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import WEEKS, DAYS, Datetime
from datetime import datetime as dt, timedelta as td


def rewards():
    @export
    def voter_is_valid(vk):
        return True

    @export
    def vote_is_valid(obj):
        if type(obj) != list:
            return False

        if len(obj) != 4:
            return False

        s = 0
        for o in obj:
            if type(o) != int:
                return False
            if o < 0:
                return False
            s += o

        if s != 100:
            return False

        return True

    @export
    def new_policy_value(values):
        mn = 0
        dl = 0
        bn = 0
        dev = 0

        for v in values:
            m, d, b, dv = v
            mn += m
            dl += d
            bn += b
            dev += dv

        total_votes = sum([mn, dl, bn, dev])

        mn /= total_votes
        dl /= total_votes
        bn /= total_votes
        dev /= total_votes

        return [mn, dl, bn, dev]


class TestRewards(TestCase):
    def setUp(self):
        self.c = ContractingClient()
        self.c.flush()

        with open('./contracts/election_house.s.py') as f:
            contract = f.read()

        self.c.submit(contract, name='election_house')
        self.c.submit(rewards, owner='election_house')
        self.c.raw_driver.commit()

        self.election_house = self.c.get_contract('election_house')
        self.rewards = self.c.get_contract('rewards')

        self.election_house.register_policy(policy='rewards',
                                            contract='rewards',
                                            election_interval=WEEKS * 1,
                                            voting_period=DAYS * 1,
                                            initial_value=[0.5, 0.5, 0, 0])

    def tearDown(self):
        self.c.flush()

    def test_vote_not_list_fails(self):
        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.election_house.vote(policy='rewards', value=False, environment=env)
        self.assertEqual(self.election_house.states['votes', 'rewards', 'sys'], None)

    def test_vote_list_not_ints_fails(self):
        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.election_house.vote(policy='rewards', value=['a', 'b', 'c', 'd'], environment=env)
        self.assertEqual(self.election_house.states['votes', 'rewards', 'sys'], None)

    def test_vote_list_not_4_elements_fails(self):
        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.election_house.vote(policy='rewards', value=[1, 2, 3], environment=env)
        self.assertEqual(self.election_house.states['votes', 'rewards', 'sys'], None)

    def test_vote_list_negatives_fails(self):
        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.election_house.vote(policy='rewards', value=[1, 2, 3, -1], environment=env)
        self.assertEqual(self.election_house.states['votes', 'rewards', 'sys'], None)

    def test_vote_list_sum_not_100_fails(self):
        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.election_house.vote(policy='rewards', value=[99, 0, 0, 0], environment=env)
        self.assertEqual(self.election_house.states['votes', 'rewards', 'sys'], None)

    def test_vote_list_sum_100_succeeds(self):
        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.election_house.vote(policy='rewards', value=[25, 25, 25, 25], environment=env)
        self.assertEqual(self.election_house.states['votes', 'rewards', 'sys'], [25, 25, 25, 25])

    def test_vote_finished_returns_average_sum(self):
        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.election_house.vote(policy='rewards', value=[25, 25, 25, 25], environment=env, signer='v1')
        self.election_house.vote(policy='rewards', value=[25, 0, 50, 25], environment=env, signer='v2')
        self.election_house.vote(policy='rewards', value=[25, 0, 0, 75], environment=env, signer='v3')

        env = {'now': Datetime._from_datetime(dt.today() + td(days=8))}

        self.election_house.vote(policy='rewards', value=[100, 0, 0, 0], environment=env, signer='v4')

        # Expected [175, 25, 75, 125] / 400 = [0.4375, 0.0625, 0.1875, 0.3125]

        self.assertEqual(self.election_house.states['current_value', 'rewards'], [0.4375, 0.0625, 0.1875, 0.3125])