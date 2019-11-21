import currency
import election_house

candidate_state = Hash()
candidate_votes = Variable()

no_confidence_state = Hash()
no_confidence_votes = Variable()
to_be_relinquished = Variable()

STAMP_COST = 20_000
MASTER_COST = 100_000

@construct
def seed():
    to_be_relinquished.set([])
    no_confidence_votes.set({})

###
# STAKING
###
@export
def register():
    # Make sure someone is already staked
    assert not candidate_state['registered', ctx.signer], 'Already registered.'

    currency.transfer_from(MASTER_COST, ctx.this, ctx.caller)

    candidate_state['registered', ctx.signer] = True

    cv = candidate_votes.get()
    cv[ctx.signer] = 0
    candidate_votes.set(cv)

@export
def unregister():
    mns = election_house.get_policy('masternodes')

    assert ctx.caller not in mns, "Can't unstake if in governance."
    assert candidate_state['registered', ctx.signer], 'Not registered.'

    currency.transfer(MASTER_COST, ctx.caller)
### ### ###

###
# VOTE CANDIDATE
###
@export
def vote_candidate(address):
    assert candidate_state['registered', address]

    # Determine if caller can vote
    v = candidate_state['last_voted', ctx.signer]
    assert now - v > DAYS * 1 or v is None, 'Voting again too soon.'

    # Deduct small vote fee
    vote_cost = STAMP_COST / election_house.get_policy('stamp_cost')
    currency.transfer_from(vote_cost, ctx.signer, 'blackhole')

    # Update last voted variable
    candidate_state['last_voted', ctx.signer] = now

    # Update vote dict
    cv = candidate_votes.get()
    cv[address] += 1
    candidate_votes.set(cv)

@export
def top_masternode():
    cv = candidate_votes.get()

    if len(_q) == 0:
        return None

    top = sorted(cv.items(), key=lambda x: x[1], reverse=True)

    return top[0][0]

@export
def pop_top():
    assert ctx.caller == 'masternodes', 'Wrong smart contract caller.'

    top = top_masternode()

    cv = candidate_votes.get()
    del cv[top]
    candidate_votes.set(cv)
### ### ###

###
# NO CONFIDENCE VOTES
###
@export
def vote_no_confidence(address):
    # Determine if caller can vote
    v = no_confidence_state['last_voted', ctx.signer]
    assert now - v > DAYS * 1 or v is None, 'Voting again too soon.'

    # Deduct small vote fee
    vote_cost = STAMP_COST / election_house.get_policy('stamp_cost')
    currency.transfer_from(vote_cost, ctx.signer, 'blackhole')

    # Update last voted variable
    no_confidence_state['last_voted', ctx.signer] = now

    # Update vote dict
    nc = no_confidence_votes.get()

    if nc.get(address) is None:
        nc[address] = 1
    else:
        nc[address] += 1

    no_confidence_votes.set(nc)

@export
def last_masternode():
    r = to_be_relinquished.get()
    if len(r) > 0:
        return r[0]

    nc = no_confidence_votes.get()
    last = sorted(nc.items(), key=lambda x: x[1], reverse=True)
    return last[0][0]


@export
def pop_last():
    assert ctx.caller == 'masternodes', 'Wrong smart contract caller.'

    r = to_be_relinquished.get()

    if len(r) > 0:
        r.pop(0)
        to_be_relinquished.set(r)

    else:
        last = last_masternode()

        nc = no_confidence_votes.get()
        del nc[last]
        no_confidence_votes.set(nc)

@export
def relinquish():
    assert ctx.signer in election_house.get_policy('masternodes')

    r = to_be_relinquished.get()
    r.append(ctx.signer)
    to_be_relinquished.set(r)
### ### ###
