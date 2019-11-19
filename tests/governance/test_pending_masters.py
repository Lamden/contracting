from unittest import TestCase
from contracting.client import ContractingClient

def pending_masters():
    import currency
    import election_house

    S = Hash()
    Q = Variable()
    STAMP_COST = 20_000

    @construct
    def seed():
        # Set as empty list
        Q.set({})

    @export
    def register():
        # Make sure someone is already staked
        assert not S['registered', ctx.signer], 'Already registered.'

        S['registered', ctx.signer] = True

        q = Q.get()
        q[ctx.signer] = 0
        Q.set(q)

    @export
    def vote(address):
        assert S['registered', address]

        # Determine if caller can vote
        v = S['last_voted', ctx.signer]
        assert now - v > DAYS * 1 or v is None, 'Voting again too soon.'

        # Deduct small vote fee
        vote_cost = STAMP_COST / election_house.get_policy('stamp_cost')
        currency.transfer_from(vote_cost, ctx.signer, 'blackhole')

        # Update last voted variable
        S['last_voted', ctx.signer] = now

        # Update vote dict
        q = Q.get()
        q[address] += 1
        Q.set(q)

    @export
    def top_masternode():
        q = Q.get()

        if len(q) == 0:
            return None

        top = sorted(q.items(), key=lambda x: x[1], reverse=True)

        return top[0][0]

    @export
    def pop_top():
        assert ctx.caller == 'masternodes', 'Wrong smart contract caller.'

        top = top_masternode()

        q = Q.get()
        del q[top]
        Q.set(q)


class TestPendingMasters(TestCase):
    def setUp(self):
        self.client = ContractingClient()

        f = open('./contracts/currency.s.py')
        self.client.submit(f.read(), 'currency')
        f.close()

        f = open('./contracts/election_house.s.py')
        self.client.submit(f.read(), 'election_house')
        f.close()

        self.client.submit(pending_masters)

        self.pending_masters = self.client.get_contract(name='pending_masters')

    def tearDown(self):
        self.client.flush()

    def test_init(self):
        pass
