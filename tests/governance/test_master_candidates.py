from unittest import TestCase
from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import Timedelta, DAYS, WEEKS, Datetime
from datetime import datetime as dt, timedelta as td


def master_candidates():
    import currency
    import election_house

    candidate_state = Hash()
    candidate_votes = Variable()

    no_confidence_state = Hash()
    no_confidence_votes = Variable()
    to_be_relinquished = Variable()

    STAMP_COST = 20_000
    MASTER_COST = 100_000

    controller = Variable()

    @construct
    def seed(masternode_contract='masternodes'):
        controller.set(masternode_contract)

        candidate_votes.set({})
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
        mns = election_house.current_value_for_policy(controller.get())

        assert candidate_state['registered', ctx.signer], 'Not registered.'
        assert ctx.caller not in mns, "Can't unstake if in governance."

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
        assert v is None or now - v > datetime.DAYS * 1, 'Voting again too soon.'

        # Deduct small vote fee
        vote_cost = STAMP_COST / election_house.current_value_for_policy('stamp_cost')
        currency.transfer_from(vote_cost, 'blackhole', ctx.signer)

        # Update last voted variable
        candidate_state['last_voted', ctx.signer] = now

        # Update vote dict
        cv = candidate_votes.get()
        cv[address] += 1
        candidate_votes.set(cv)

    @export
    def top_masternode():
        cv = candidate_votes.get()

        if len(cv) == 0:
            return None

        top = sorted(cv.items(), key=lambda x: x[1], reverse=True)

        return top[0][0]

    @export
    def pop_top():
        assert ctx.caller == controller.get(), 'Wrong smart contract caller.'

        top = top_masternode()

        if top is None:
            return None

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
        assert ctx.caller == controller.get(), 'Wrong smart contract caller.'

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
        assert ctx.signer in election_house.get_policy(controller.get())

        r = to_be_relinquished.get()
        r.append(ctx.signer)
        to_be_relinquished.set(r)
    ### ### ###


class TestPendingMasters(TestCase):
    def setUp(self):
        self.client = ContractingClient()

        f = open('./contracts/currency.s.py')
        self.client.submit(f.read(), 'currency')
        f.close()

        f = open('./contracts/election_house.s.py')
        self.client.submit(f.read(), 'election_house')
        f.close()

        f = open('./contracts/stamp_cost.s.py')
        self.client.submit(f.read(), 'stamp_cost', owner='election_house', constructor_args={'initial_rate': 20_000})
        f.close()

        f = open('./contracts/masternodes.s.py')
        self.client.submit(f.read(), 'masternodes', owner='election_house', constructor_args={'initial_masternodes':
                                                                                              ['stux', 'raghu'],
                                                                                              'initial_open_seats': 0})
        f.close()

        self.client.submit(master_candidates)

        self.master_candidates = self.client.get_contract(name='master_candidates')
        self.currency = self.client.get_contract(name='currency')
        self.masternodes = self.client.get_contract(name='masternodes')

        self.stamp_cost = self.client.get_contract(name='stamp_cost')
        self.election_house = self.client.get_contract(name='election_house')
        self.election_house.register_policy(contract='stamp_cost')
        self.election_house.register_policy(contract='masternodes')

    def tearDown(self):
        self.client.flush()

    def test_register(self):
        self.currency.approve(signer='stu', amount=100_000, to='master_candidates')
        self.master_candidates.register(signer='stu')
        q = self.master_candidates.candidate_votes.get()

        self.assertEqual(q['stu'], 0)
        self.assertEqual(self.currency.balances['master_candidates'], 100_000)
        self.assertEqual(self.master_candidates.candidate_state['registered', 'stu'], True)

    def test_double_register_raises_assert(self):
        self.currency.approve(signer='stu', amount=100_000, to='master_candidates')
        self.master_candidates.register(signer='stu')
        self.currency.approve(signer='stu', amount=100_000, to='master_candidates')

        with self.assertRaises(AssertionError):
            self.master_candidates.register(signer='stu')

    def test_unregister_returns_currency(self):
        b1 = self.currency.balances['stu']
        self.currency.approve(signer='stu', amount=100_000, to='master_candidates')
        self.master_candidates.register(signer='stu')

        self.assertEqual(self.currency.balances['stu'], b1 - 100_000)

        self.master_candidates.unregister(signer='stu')

        self.assertEqual(self.currency.balances['stu'], b1)

    def test_unregister_if_in_masternodes_throws_assert(self):
        self.currency.approve(signer='stu', amount=100_000, to='master_candidates')
        self.master_candidates.register(signer='stu')

        self.masternodes.S['masternodes'] = ['stu', 'raghu']

        with self.assertRaises(AssertionError):
            self.master_candidates.unregister()

    def test_unregister_if_not_registered_throws_assert(self):
        with self.assertRaises(AssertionError):
            self.master_candidates.unregister()

    def test_vote_for_someone_not_registered_throws_assertion_error(self):
        with self.assertRaises(AssertionError):
            self.master_candidates.vote_candidate(address='stu')

    def test_vote_for_someone_registered_deducts_tau_and_adds_vote(self):
        # Give joe money
        self.currency.transfer(signer='stu', amount=100_000, to='joe')

        # Joe Allows Spending
        self.currency.approve(signer='joe', amount=100_000, to='master_candidates')

        self.master_candidates.register(signer='joe')

        self.currency.approve(signer='stu', amount=10_000, to='master_candidates')

        env = {'now': Datetime._from_datetime(dt.today())}

        stu_bal = self.currency.balances['stu']

        self.master_candidates.vote_candidate(signer='stu', address='joe', environment=env)

        self.assertEqual(self.currency.balances['stu'], stu_bal - 1)
        self.assertEqual(self.master_candidates.candidate_votes.get()['joe'], 1)
        self.assertEqual(self.currency.balances['blackhole'], 1)
        self.assertEqual(self.master_candidates.candidate_state['last_voted', 'stu'], env['now'])

    def test_voting_again_too_soon_throws_assertion_error(self):
        # Give joe money
        self.currency.transfer(signer='stu', amount=100_000, to='joe')

        # Joe Allows Spending
        self.currency.approve(signer='joe', amount=100_000, to='master_candidates')

        self.master_candidates.register(signer='joe')

        self.currency.approve(signer='stu', amount=10_000, to='master_candidates')

        env = {'now': Datetime._from_datetime(dt.today())}

        self.master_candidates.vote_candidate(signer='stu', address='joe', environment=env)

        with self.assertRaises(AssertionError):
            self.master_candidates.vote_candidate(signer='stu', address='joe', environment=env)

    def test_voting_again_after_waiting_one_day_works(self):
        # Give joe money
        self.currency.transfer(signer='stu', amount=100_000, to='joe')

        # Joe Allows Spending
        self.currency.approve(signer='joe', amount=100_000, to='master_candidates')

        self.master_candidates.register(signer='joe')

        self.currency.approve(signer='stu', amount=10_000, to='master_candidates')

        stu_bal = self.currency.balances['stu']

        env = {'now': Datetime._from_datetime(dt.today())}

        self.master_candidates.vote_candidate(signer='stu', address='joe', environment=env)

        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.master_candidates.vote_candidate(signer='stu', address='joe', environment=env)

        self.assertEqual(self.currency.balances['stu'], stu_bal - 2)
        self.assertEqual(self.master_candidates.candidate_votes.get()['joe'], 2)

        self.assertEqual(self.currency.balances['blackhole'], 2)

        self.assertEqual(self.master_candidates.candidate_state['last_voted', 'stu'], env['now'])

    def test_top_masternode_returns_none_if_no_candidates(self):
        self.assertIsNone(self.master_candidates.top_masternode())

    def test_top_masternode_returns_joe_if_registered_but_no_votes(self):
        self.currency.transfer(signer='stu', amount=100_000, to='joe')  # Give joe money
        self.currency.approve(signer='joe', amount=100_000, to='master_candidates')  # Joe Allows Spending
        self.master_candidates.register(signer='joe')  # Register Joe

        self.assertEqual(self.master_candidates.top_masternode(), 'joe')  # Joe is the current top spot

    def test_top_masternode_returns_bob_if_joe_and_bob_registered_but_bob_has_votes(self):
        self.currency.transfer(signer='stu', amount=100_000, to='joe')  # Give joe money
        self.currency.approve(signer='joe', amount=100_000, to='master_candidates')  # Joe Allows Spending
        self.master_candidates.register(signer='joe')  # Register Joe

        self.currency.transfer(signer='stu', amount=100_000, to='bob')  # Give Bob money
        self.currency.approve(signer='bob', amount=100_000, to='master_candidates')  # Bob Allows Spending
        self.master_candidates.register(signer='bob')  # Register Bob

        self.currency.approve(signer='stu', amount=10_000, to='master_candidates')  # Stu approves spending to vote
        env = {'now': Datetime._from_datetime(dt.today())}
        self.master_candidates.vote_candidate(signer='stu', address='bob', environment=env)  # Stu votes for Bob

        self.assertEqual(self.master_candidates.top_masternode(), 'bob')  # bob is the current top spot

    def test_top_masternode_returns_joe_if_joe_and_bob_registered_but_joe_first_and_no_votes(self):
        self.currency.transfer(signer='stu', amount=100_000, to='joe')  # Give joe money
        self.currency.approve(signer='joe', amount=100_000, to='master_candidates')  # Joe Allows Spending
        self.master_candidates.register(signer='joe')  # Register Joe

        self.currency.transfer(signer='stu', amount=100_000, to='bob')  # Give Bob money
        self.currency.approve(signer='bob', amount=100_000, to='master_candidates')  # Bob Allows Spending
        self.master_candidates.register(signer='bob')  # Register Bob

        self.assertEqual(self.master_candidates.top_masternode(), 'joe')  # Joe is the current top spot

    def test_pop_top_fails_if_not_masternodes_contract(self):
        with self.assertRaises(AssertionError):
            self.master_candidates.pop_top()

    def test_pop_top_doesnt_fail_if_masternode_contract(self):
        self.master_candidates.pop_top(signer='masternodes')

    def test_pop_top_deletes_bob_if_pop_is_top_masternode(self):
        self.currency.transfer(signer='stu', amount=100_000, to='joe')  # Give joe money
        self.currency.approve(signer='joe', amount=100_000, to='master_candidates')  # Joe Allows Spending
        self.master_candidates.register(signer='joe')  # Register Joe

        self.currency.transfer(signer='stu', amount=100_000, to='bob')  # Give Bob money
        self.currency.approve(signer='bob', amount=100_000, to='master_candidates')  # Bob Allows Spending
        self.master_candidates.register(signer='bob')  # Register Bob

        self.currency.approve(signer='stu', amount=10_000, to='master_candidates')  # Stu approves spending to vote
        env = {'now': Datetime._from_datetime(dt.today())}
        self.master_candidates.vote_candidate(signer='stu', address='bob', environment=env)  # Stu votes for Bob

        self.assertEqual(self.master_candidates.top_masternode(), 'bob')  # bob is the current top spot

        self.assertIsNotNone(self.master_candidates.candidate_votes.get().get('bob'))

        self.master_candidates.pop_top(signer='masternodes')

        self.assertIsNone(self.master_candidates.candidate_votes.get().get('bob'))

    def test_pop_top_returns_none_if_noone_registered(self):
        self.assertIsNone(self.master_candidates.pop_top(signer='masternodes'))
