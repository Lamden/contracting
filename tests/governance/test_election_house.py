from unittest import TestCase
from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Timedelta, DAYS, WEEKS

def election_house():
    # Convenience
    I = importlib

    # Subhash IDs
    CONTRACT = 'contract'

    VOTES = 'votes'
    CURRENT_VALUE = 'current_value'

    IN_ELECTION = 'in_election'
    ELECTION_START_TIME = 'election_start_time'
    LAST_ELECTION_END_TIME = 'election_end_time'
    VOTING_PERIOD = 'voting_period'
    ELECTION_INTERVAL = 'election_interval'

    # Main state datum
    states = Hash()

    # Policy interface
    policy_interface = [
        I.Func('voter_is_valid', args=('vk',)),
        I.Func('vote_is_valid', args=('obj',)),
        I.Func('new_policy_value', args=('values',)),
    ]

    @export
    def register_policy(policy, contract, election_interval, voting_period):
        # Make sure the policy is not registered
        if states[CONTRACT, policy] is None:

            # Attempt to import the contract to make sure it is already submitted
            p = I.import_module(contract)

            # Assert ownership is election_house and interface is correct
            assert I.owner_of(p) == ctx.this, \
                'Election house must control the policy contract!'

            assert I.enforce_interface(p, policy_interface), \
                'Policy contract does not follow the correct interface'

            states[CONTRACT, policy] = contract
            states[ELECTION_INTERVAL, policy] = election_interval
            states[VOTING_PERIOD, policy] = voting_period

            reset_election(policy)
        else:
            raise Exception('Policy already registered')

    @export
    def get_policy(policy: str):
        # Simple getter
        return states[CURRENT_VALUE, policy]

    @export
    def vote(policy, value):
        # Verify policy has been registered
        assert states[CONTRACT, policy] is not None, 'Invalid policy.'

        # Import the module associated with this policy
        p = I.import_module(states[CONTRACT, policy])

        if states[IN_ELECTION, policy] and p.voter_is_valid(ctx.caller) and p.vote_is_valid(value):

            states[VOTES, policy, ctx.caller] = value

            # If between now and the start time, the voting interval length has passed, tally the votes and set the
            # new value. Reset the policy election state.
            if now - states[ELECTION_START_TIME, policy] >= states[VOTING_PERIOD, policy]:
                votes = states.all(VOTES, policy)
                states[CURRENT_VALUE, policy] = p.new_policy_value(votes)
                reset_election(policy)

        else:
            if now - states[LAST_ELECTION_END_TIME, policy] > states[ELECTION_INTERVAL, policy]:
                # Start the election and set the proper variables
                states[ELECTION_START_TIME, policy] = now
                states[IN_ELECTION, policy] = True

                states[VOTES, policy, ctx.caller] = value
            else:
                raise Exception('Outside of governance parameters.')

    def reset_election(policy: str):
        states[LAST_ELECTION_END_TIME, policy] = now
        states[IN_ELECTION, policy] = False
        states.clear(VOTES, policy)


def good_policy():
    @export
    def voter_is_valid(vk):
        return True

    @export
    def vote_is_valid(obj):
        return True

    @export
    def new_policy_value(values):
        return values[0]


class TestElectionHouse(TestCase):
    def setUp(self):
        self.client = ContractingClient()
        self.client.submit(election_house)
        self.election_house = self.client.get_contract('election_house')

    def tearDown(self):
        self.client.flush()

    def test_submit_policy_works(self):
        self.client.submit(good_policy, owner='election_house')

        self.election_house.register_policy(policy='testing',
                                            contract='good_policy',
                                            election_interval=WEEKS*1,
                                            voting_period=DAYS*1)

        self.assertEqual(self.election_house.states['contract', 'testing'], 'good_policy')
        self.assertEqual(self.election_house.states['election_interval', 'testing'], WEEKS*1)
        self.assertEqual(self.election_house.states['voting_period', 'testing'], DAYS*1)
        self.assertEqual(self.election_house.states['in_election', 'testing'], False)

