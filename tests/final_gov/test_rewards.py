from unittest import TestCase
from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Timedelta, DAYS, WEEKS, Datetime
from datetime import datetime as dt, timedelta as td


class TestRewards(TestCase):
    def setUp(self):
        self.client = ContractingClient()
        self.client.flush()

        with open('./contracts/election_house.s.py') as f:
            contract = f.read()

        self.client.submit(contract, name='election_house')

        with open('./contracts/rewards.s.py') as f:
            contract = f.read()

        self.client.submit(contract, name='rewards')

        with open('./contracts/members.s.py') as f:
            contract = f.read()

        self.client.submit(contract, name='masternodes', owner='election_house', constructor_args={
            'initial_members': ['a', 'b'],
            'candidate': 'elect_masters'
        })

        self.client.submit(contract, name='delegates', owner='election_house', constructor_args={
            'initial_members': ['c', 'd', 'e', 'f'],
            'candidate': 'elect_delegates'
        })

        self.election_house = self.client.get_contract('election_house')
        self.election_house.register_policy(contract='masternodes')
        self.election_house.register_policy(contract='delegates')

        self.rewards = self.client.get_contract('rewards')

    def test_initial_value(self):
        self.assertListEqual(self.rewards.current_value(), [0.5, 0.5, 0, 0])

    def test_validate_vote_fails_if_not_node(self):
        with self.assertRaises(AssertionError):
            self.rewards.run_private_function(
                f='validate_vote',
                signer='stu',
                vk='stu',
                obj=[100, 0, 0, 0]
            )

    def test_validate_vote_fails_if_not_list(self):
        with self.assertRaises(AssertionError):
            self.rewards.run_private_function(
                f='validate_vote',
                signer='stu',
                vk='a',
                obj=(100, 0, 0, 0)
            )

    def test_validate_vote_fails_if_not_4_elements(self):
        with self.assertRaises(AssertionError):
            self.rewards.run_private_function(
                f='validate_vote',
                signer='stu',
                vk='a',
                obj=[100, 0, 0]
            )

    def test_validate_vote_fails_if_not_pos_int(self):
        with self.assertRaises(AssertionError):
            self.rewards.run_private_function(
                f='validate_vote',
                signer='stu',
                vk='a',
                obj=[101, 0, 0, -1]
            )

    def test_validate_vote_fails_if_not_sum_100(self):
        with self.assertRaises(AssertionError):
            self.rewards.run_private_function(
                f='validate_vote',
                signer='stu',
                vk='a',
                obj=[101, 0, 0, 0]
            )

    def test_validate_vote_succeeds(self):
        self.rewards.run_private_function(
            f='validate_vote',
            signer='stu',
            vk='a',
            obj=[100, 0, 0, 0]
        )

    def test_validate_vote_fails_double_vote(self):
        self.rewards.quick_write(variable='S', value=True, args=['has_voted', 'a'])

        with self.assertRaises(AssertionError):
            self.rewards.run_private_function(
                f='validate_vote',
                signer='stu',
                vk='a',
                obj=[100, 0, 0, 0]
            )

    def test_tally_vote_sets_has_voted_true(self):
        self.rewards.run_private_function(
            f='tally_vote',
            signer='stu',
            vk='a',
            obj=[100, 0, 0, 0]
        )

        self.assertTrue(self.rewards.S['has_voted', 'a'])

    def test_tally_votes_adds_to_each_party(self):
        self.rewards.run_private_function(
            f='tally_vote',
            signer='stu',
            vk='a',
            obj=[26, 30, 20, 24]
        )

        self.assertEqual(self.rewards.S['current_votes', 'masternodes'], 26)
        self.assertEqual(self.rewards.S['current_votes', 'delegates'], 30)
        self.assertEqual(self.rewards.S['current_votes', 'blackhole'], 20)
        self.assertEqual(self.rewards.S['current_votes', 'foundation'], 24)

    def test_votes_starts_new_election_if_first_vote(self):
        self.rewards.vote(vk='a', obj=[26, 30, 20, 24])

        self.assertEqual(self.rewards.S['min_votes_required'], 5)
        self.assertEqual(self.rewards.S['vote_count'], 1)

    def test_election_is_over_if_more_than_max_time_past_first_vote(self):
        self.rewards.vote(vk='a', obj=[26, 30, 20, 24])

        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        res = self.rewards.run_private_function(
            f='election_is_over',
            signer='stu',
            environment=env
        )

        self.assertTrue(res)

    def test_election_over_if_more_than_min_required_vote(self):
        self.rewards.vote(vk='a', obj=[26, 30, 20, 24])
        self.rewards.vote(vk='b', obj=[26, 30, 20, 24])
        self.rewards.vote(vk='c', obj=[26, 30, 20, 24])
        self.rewards.vote(vk='d', obj=[26, 30, 20, 24])
        self.rewards.vote(vk='e', obj=[26, 30, 20, 24])

        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        res = self.rewards.run_private_function(
            f='election_is_over',
            signer='stu',
            environment=env
        )

        self.assertTrue(res)

    def test_second_vote_simply_tallies_vote(self):
        self.rewards.vote(vk='a', obj=[26, 30, 20, 24])
        self.rewards.vote(vk='b', obj=[50, 50, 0, 0])

        self.assertEqual(self.rewards.S['current_votes', 'masternodes'], 76)
        self.assertEqual(self.rewards.S['current_votes', 'delegates'], 80)
        self.assertEqual(self.rewards.S['current_votes', 'blackhole'], 20)
        self.assertEqual(self.rewards.S['current_votes', 'foundation'], 24)

    def test_complete_election_updates_value(self):
        self.rewards.vote(vk='a', obj=[26, 30, 20, 24])
        self.rewards.vote(vk='b', obj=[50, 50, 0, 0])
        self.rewards.vote(vk='c', obj=[20, 30, 10, 40])
        self.rewards.vote(vk='d', obj=[15, 40, 20, 25])
        self.rewards.vote(vk='e', obj=[0, 2, 8, 90])

        self.assertIsNone(self.rewards.S['election_start'])

        self.assertListEqual(self.rewards.current_value(), [0.222, 0.304, 0.116, 0.358])
