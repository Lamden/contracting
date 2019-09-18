from unittest import TestCase
from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Timedelta, DAYS, WEEKS, Datetime
from datetime import datetime as dt, timedelta as td

def stamps():
    import election_house

    S = Hash()

    ELECTION_INTERVAL = datetime.DAYS * 3
    VOTING_PERIOD = datetime.DAYS * 1

    @construct
    def seed(initial_rate):
        S['rate'] = initial_rate
        reset()

    @export
    def current_value():
        return S['rate']

    @export
    def vote(vk, obj):
        # Check to make sure that there is an election
        if S['in_election']:
            assert_vote_is_valid(vk, obj)
            S['votes', vk] = obj

            if now - S['election_start_time'] >= VOTING_PERIOD:
                # Tally votes and set the new value
                result = median(S['votes'].all())
                S['rate'] = result

                reset()
        else:
            # If there isn't, it might be time for a new one, so start it if so.
            # You can then submit your vote as well.
            if now - S['last_election_end_time'] > ELECTION_INTERVAL:
                # Start the election and set the proper variables
                S['election_start_time'] = now
                S['in_election'] = True

                assert_vote_is_valid(vk, obj)
                S['votes', vk] = obj
            else:
                raise Exception('Outside of governance parameters.')

    def assert_vote_is_valid(vk, obj):
        current_rate = S['rate']
        assert type(obj) == int, 'Vote is not an int'
        assert current_rate / 2 <= obj <= current_rate * 2, 'Proposed rate is not within proper boundaries.'

        masternode_policy = election_house.current_value_for_policy(policy='masternodes')

        assert vk in masternode_policy['masternodes'], 'VK is not a masternode!'
        assert S['vote', vk] is None, 'VK already voted!'

    def median(vs):
        sorted_votes = sorted(vs)
        index = (len(sorted_votes) - 1) // 2

        if len(sorted_votes) % 2:
            return sorted_votes[index]
        else:
            return (sorted_votes[index] + sorted_votes[index + 1]) / 2

    def reset():
        S['last_election_end_time'] = now
        S['in_election'] = False
        S.clear('votes')


class TestStamps(TestCase):
    def setUp(self):
        self.client = ContractingClient()

        with open('./contracts/election_house.s.py') as f:
            contract = f.read()

        self.client.submit(contract, name='election_house')
        self.election_house = self.client.get_contract('election_house')

    def tearDown(self):
        self.client.flush()

    def test_init(self):
        self.client.submit(stamps, constructor_args={
            'initial_rate': 10000,
        })

        stamps_contract = self.client.get_contract('stamps')

        self.assertEqual(stamps_contract.current_value(), 10000)

    def test_vote_is_not_int_fails(self):
        pass

    def test_vote_is_less_than_half_current_rate_fails(self):
        pass

    def test_vote_is_greater_than_double_current_rate_fails(self):
        pass

    def test_vk_is_not_masternode_fails(self):
        pass

    def test_vk_has_already_voted_fails(self):
        pass