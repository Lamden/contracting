from unittest import TestCase
from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import WEEKS, DAYS, Datetime
from datetime import datetime as dt, timedelta as td


def new():
    votes = Hash()
    value = Variable()

    @export
    def current_value():
        return value.get()

    @export
    def vote(vk, obj):
        raise NotImplementedError

    @export
    def start():
        pass

    def finish():
        pass

    def is_in_election():
        pass

    def can_start_election():
        pass

def masternodes():
    @export
    def voter_is_valid(vk):
        return True

    @export
    def vote_is_valid(obj):
        return True

    @export
    def new_policy_value(values):
        return None

class TestMasternodes(TestCase):
    def setUp(self):
        self.c = ContractingClient()
        self.c.flush()

        with open('./contracts/election_house.s.py') as f:
            contract = f.read()

        self.c.submit(contract, name='election_house')
        self.c.submit(masternodes, owner='election_house')
        self.c.raw_driver.commit()

        self.election_house = self.c.get_contract('election_house')
        self.rewards = self.c.get_contract('masternodes')

        self.election_house.register_policy(policy='masternodes',
                                            contract='masternodes',
                                            election_interval=WEEKS * 1,
                                            voting_period=DAYS * 1,
                                            initial_value=[])