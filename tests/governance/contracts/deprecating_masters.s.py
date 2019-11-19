import currency
import election_house

S = Hash()
relinquish = Variable()
no_confidence = Variable()

STAMP_COST = 20_000

@construct
def seed():
    relinquish.set([])
    no_confidence.set({})

@export
def vote(address):
    # Determine if caller can vote
    v = S['last_voted', ctx.signer]
    assert now - v > DAYS * 1 or v is None, 'Voting again too soon.'

    # Deduct small vote fee
    vote_cost = STAMP_COST / election_house.get_policy('stamp_cost')
    currency.transfer_from(vote_cost, ctx.signer, 'blackhole')

    # Update last voted variable
    S['last_voted', ctx.signer] = now

    # Update vote dict
    nc = no_confidence.get()

    if nc.get(address) is None:
        nc[address] = 1
    else:
        nc[address] += 1

    no_confidence.set(nc)

@export
def last_masternode():
    r = relinquish.get()
    if len(r) > 0:
        return r[0]

    nc = no_confidence.get()
    last = sorted(nc.items(), key=lambda x: x[1], reverse=True)
    return last[0][0]


@export
def pop_last():
    assert ctx.caller == 'masternodes', 'Wrong smart contract caller.'

    r = relinquish.get()

    if len(r) > 0:
        r.pop(0)
        relinquish.set(r)

    else:
        last = last_masternode()

        nc = no_confidence.get()
        del nc[last]
        no_confidence.set(nc)

@export
def relinquish():
    assert ctx.signer in election_house.get_policy('masternodes')

    r = relinquish.get()
    r.append(ctx.signer)
    relinquish.set(r)
