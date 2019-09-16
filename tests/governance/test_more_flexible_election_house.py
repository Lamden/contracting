from unittest import TestCase
from contracting.client import ContractingClient

def election_house():
    # Convenience
    I = importlib

    # Main state datum
    contract_to_policy = Hash()
    policy_to_contract = Hash()

    # Policy interface
    policy_interface = [
        I.Func('vote', args=('vk', 'obj')),
        I.Func('current_value')
    ]

    @export
    def register_policy(policy_name, contract):
        if policy_to_contract[policy_name] is None and contract_to_policy[contract] is None:
            # Attempt to import the contract to make sure it is already submitted
            p = I.import_module(contract)

            # Assert ownership is election_house and interface is correct
            assert I.owner_of(p) == ctx.this, \
                'Election house must control the policy contract!'

            assert I.enforce_interface(p, policy_interface), \
                'Policy contract does not follow the correct interface'

            policy_to_contract[policy_name] = contract
            contract_to_policy[contract] = policy_name
        else:
            raise Exception('Policy already registered')

    @export
    def current_value_for_policy(policy_name: str):
        contract = policy_to_contract[policy_name]
        p = I.import_module(contract)

        return p.current_value()

    @export
    def vote(policy_name, value):
        # Verify policy has been registered
        contract_name = policy_to_contract[policy_name]
        assert contract_name is not None, 'Invalid policy.'

        p = I.import_module(contract_name)

        p.vote(vk=ctx.caller, obj=value)

def test_policy():
    value = Variable()
    @export
    def current_value():
        return value.get()

    @export
    def vote(vk, obj):
        value.set(obj)

    def another_func():
        print('this shouldnt matter')


class TestBetterElectionHouse(TestCase):
    def setUp(self):
        self.client = ContractingClient()
        self.client.submit(election_house)
        self.election_house = self.client.get_contract(name='election_house')

    def tearDown(self):
        self.client.flush()

    def test_init(self):
        pass