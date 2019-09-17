from unittest import TestCase
from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Timedelta, DAYS, WEEKS, Datetime
from datetime import datetime as dt, timedelta as td

def masternodes():
    INTRODUCE_MOTION = 'introduce_motion'
    VOTE_ON_MOTION = 'vote_on_motion'

    NO_MOTION = 0
    ADD_MASTER = 1
    REMOVE_MASTER = 2
    ADD_SEAT = 3
    REMOVE_SEAT = 4

    VOTING_PERIOD = datetime.DAYS * 1

    S = Hash()

    @construct
    def seed(initial_masternodes, initial_open_seats):
        S['masternodes'] = initial_masternodes
        S['open_seats'] = initial_open_seats

        S['votes'] = 0
        S['current_motion'] = NO_MOTION
        S['motion_opened'] = now

    @export
    def current_value():
        return {
            'masternodes': S['masternodes'],
            'open_seats': S['open_seats']
        }

    @export
    def vote(vk, obj):
        arg = None
        try:
            action, position, arg = obj
        except ValueError:
            action, position = obj

        assert_vote_is_valid(vk, action, position, arg)

        if action == INTRODUCE_MOTION:
            introduce_motion(position, arg)

        else:
            assert S['current_motion'] != NO_MOTION, 'No motion proposed.'

            if position is True:
                S['votes'] += 1
                S['positions', ctx.caller] = position

            if S['votes'] >= len(S['masternodes']) // 2 + 1:
                pass_current_motion()
                reset()

            if now - S['motion_opened'] >= VOTING_PERIOD:
                reset()

    def pass_current_motion():
        current_motion = S['current_motion']

        if current_motion == ADD_MASTER:
            S['masternodes'].append(S['master_in_question'])
            S['open_seats'] -= 1

        elif current_motion == REMOVE_MASTER:
            S['masternodes'].remove(S['master_in_question'])
            S['open_seats'] += 1

        elif current_motion == ADD_SEAT:
            S['open_seats'] += 1

        elif current_motion == REMOVE_SEAT:
            S['open_seats'] -= 1

    def introduce_motion(position, arg):
        if position == ADD_MASTER or position == REMOVE_SEAT:
            assert S['open_seats'] > 0, 'No open seats to add or remove.'

        if position == ADD_MASTER or position == REMOVE_MASTER:
            S['master_in_question'] = arg

        S['current_motion'] = position
        S['motion_opened'] = now

    def assert_vote_is_valid(vk, action, position, arg=None):
        assert vk in S['masternodes'], 'Not a masternode.'

        assert action in [INTRODUCE_MOTION, VOTE_ON_MOTION], 'Invalid action.'

        if action == INTRODUCE_MOTION:
            assert S['current_motion'] == NO_MOTION, 'Already in motion.'
            assert 0 < position <= REMOVE_SEAT, 'Invalid motion.'
            if position == ADD_MASTER or position == REMOVE_MASTER:
                assert_vk_is_valid(arg)

        elif action == VOTE_ON_MOTION:
            assert type(position) == bool, 'Invalid position'

    def assert_vk_is_valid(vk):
        assert vk is not None, 'No VK provided.'
        assert type(vk) == str, 'VK not a string.'
        assert len(vk) == 64, 'VK is not 64 characters.'
        int(vk, 16)

    def reset():
        S['current_motion'] = NO_MOTION
        S['master_in_question'] = None
        S['votes'] = 0
        S.clear('positions')


class TestMasternodePolicy(TestCase):
    def setUp(self):
        self.client = ContractingClient()

        with open('./contracts/election_house.s.py') as f:
            contract = f.read()

        self.client.submit(contract, name='election_house')
        self.election_house = self.client.get_contract('election_house')

    def tearDown(self):
        self.client.flush()

    def test_init(self):
        self.client.submit(masternodes, owner='election_house', constructor_args={
            'initial_masternodes': [1, 2, 3],
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        self.assertEqual(mn_contract.current_value(signer='election_house'), {
            'masternodes': [1, 2, 3],
            'open_seats': 0
        })

        self.assertEqual(mn_contract.S['votes'], 0)
        self.assertEqual(mn_contract.S['current_motion'], 0)

    def test_voter_not_masternode_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        with self.assertRaises(AssertionError):
            mn_contract.run_private_function(
                f='assert_vote_is_valid',
                vk='sys',
                action='introduce_motion',
                position=1
            )

    def test_vote_invalid_action_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        with self.assertRaises(AssertionError):
            mn_contract.run_private_function(
                f='assert_vote_is_valid',
                vk=1,
                action='xxx',
                position=1
            )

    def test_vote_on_motion_bool_succeeds(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        mn_contract.run_private_function(
            f='assert_vote_is_valid',
            vk=1,
            action='vote_on_motion',
            position=True
        )

    def test_action_introduce_motion_current_motion_not_no_motion_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        mn_contract.quick_write(variable='S', key='current_motion', value=1)

        with self.assertRaises(AssertionError):
            mn_contract.run_private_function(
                f='assert_vote_is_valid',
                vk=1,
                action='introduce_motion',
                position=1
            )

    def test_action_introduce_motion_out_of_range_motion_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        with self.assertRaises(AssertionError):
            mn_contract.run_private_function(
                f='assert_vote_is_valid',
                vk=1,
                action='introduce_motion',
                position=10
            )

    def test_action_introduce_motion_no_arg_provided_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        with self.assertRaises(AssertionError):
            mn_contract.run_private_function(
                f='assert_vote_is_valid',
                vk=1,
                action='introduce_motion',
                position=1
            )

    def test_action_introduce_motion_vk_not_str_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        with self.assertRaises(AssertionError):
            mn_contract.run_private_function(
                f='assert_vote_is_valid',
                vk=1,
                action='introduce_motion',
                position=1,
                arg=True
            )

    def test_action_introduce_motion_vk_not_64_chars_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        with self.assertRaises(AssertionError):
            mn_contract.run_private_function(
                f='assert_vote_is_valid',
                vk=1,
                action='introduce_motion',
                position=1,
                arg='a'
            )

    def test_action_introduce_motion_not_valid_hex_fails(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        with self.assertRaises(ValueError):
            mn_contract.run_private_function(
                f='assert_vote_is_valid',
                vk=1,
                action='introduce_motion',
                position=1,
                arg='x' * 64
            )

    def test_action_vote_on_motion_fails_if_not_bool(self):
        self.client.submit(masternodes, constructor_args={
            'initial_masternodes': [1, 2, 3],
            'initial_open_seats': 0
        })

        mn_contract = self.client.get_contract('masternodes')

        with self.assertRaises(AssertionError):
            mn_contract.run_private_function(
                f='assert_vote_is_valid',
                vk=1,
                action='vote_on_motion',
                position=1,
            )