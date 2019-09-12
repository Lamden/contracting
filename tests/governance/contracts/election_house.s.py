#
# policy_states[policy, 'in_election']
# voting_period

IN_ELECTION = 'in_election'
VOTES = 'votes'
ELECTION_START_TIME = 'election_start_time'
VOTING_PERIOD = 'voting_period'

policy_registrar = Hash()
policy_states = Hash()

policy_interface = [
    importlib.Func('voter_is_valid', args=('vk',)),
    importlib.Func('vote_is_valid', args=('obj',)),
    importlib.Func('new_policy_value', args=('values',)),
]

@export
def register_policy(policy_variable_name, policy_contract_location):
    if policy_registrar[policy_variable_name] is None:
        p = importlib.import_module(policy_contract_location)

        assert importlib.owner_of(p) == ctx.this, \
            'Election house must control the policy contract!'

        assert importlib.enforce_interface(p, policy_interface), \
            'Policy contract does not follow the correct interface'

        policy_registrar[policy_variable_name] = policy_contract_location
    else:
        raise Exception('Policy already registered')


@export
def vote(policy_variable_name, value):
    policy_contract = policy_registrar[policy_variable_name]
    assert policy_contract is not None, 'Invalid policy.'

    policy = importlib.import_module(policy_contract)

    in_election = policy_states[policy_variable_name, IN_ELECTION]
    election_start_time = policy_states[policy_variable_name, ELECTION_START_TIME]
    voting_period = policy_states[policy_variable_name, VOTING_PERIOD]


    if in_election and policy.voter_is_valid(ctx.caller) and policy.vote_is_valid(value):
        policy_states[policy_variable_name, VOTES, ctx.caller] = value

        if now - election_start_time >= voting_period:
            policy.new_policy_value()

