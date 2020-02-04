from unittest import TestCase
from contracting.client import ContractingClient

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

        f = open('./contracts/members.s.py')
        self.client.submit(f.read(), 'masternodes', owner='election_house', constructor_args={'initial_members':
                                                                                              ['stux', 'raghu']})
        f.close()

        f = open('./contracts/elect_members.s.py')
        self.client.submit(f.read(), 'elect_members')
        f.close()

        self.elect_members = self.client.get_contract(name='elect_members')
        self.currency = self.client.get_contract(name='currency')
        self.masternodes = self.client.get_contract(name='masternodes')

        self.stamp_cost = self.client.get_contract(name='stamp_cost')
        self.election_house = self.client.get_contract(name='election_house')
        self.election_house.register_policy(contract='stamp_cost')
        self.election_house.register_policy(contract='masternodes')

    def tearDown(self):
        self.client.flush()

    def test_register(self):
        self.currency.approve(signer='stu', amount=100_000, to='elect_members')
        self.elect_members.register(signer='stu')
        q = self.elect_members.candidate_state['votes', 'stu']

        self.assertEqual(q, 0)
        self.assertEqual(self.currency.balances['elect_members'], 100_000)
        self.assertEqual(self.elect_members.candidate_state['registered', 'stu'], True)

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

        print(self.master_candidates.executor.driver.pending_writes)

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

    def test_voting_no_confidence_against_non_committee_member_fails(self):
        with self.assertRaises(AssertionError):
            self.master_candidates.vote_no_confidence(address='whoknows')

    def test_vote_no_confidence_for_someone_registered_deducts_tau_and_adds_vote(self):
        self.currency.approve(signer='stu', amount=10_000, to='master_candidates')

        stu_bal = self.currency.balances['stu']

        env = {'now': Datetime._from_datetime(dt.today())}

        self.master_candidates.vote_no_confidence(signer='stu', address='raghu', environment=env) # Raghu is seeded in contract

        self.assertEqual(self.currency.balances['stu'], stu_bal - 1)
        self.assertEqual(self.master_candidates.no_confidence_votes.get()['raghu'], 1)
        self.assertEqual(self.currency.balances['blackhole'], 1)
        self.assertEqual(self.master_candidates.no_confidence_state['last_voted', 'stu'], env['now'])

    def test_voting_no_confidence_again_too_soon_throws_assertion_error(self):
        self.currency.approve(signer='stu', amount=10_000, to='master_candidates')

        env = {'now': Datetime._from_datetime(dt.today())}

        self.master_candidates.vote_no_confidence(signer='stu', address='raghu', environment=env)

        with self.assertRaises(AssertionError):
            self.master_candidates.vote_no_confidence(signer='stu', address='raghu', environment=env)

    def test_voting_no_confidence_again_after_waiting_one_day_works(self):
        self.currency.approve(signer='stu', amount=10_000, to='master_candidates')

        stu_bal = self.currency.balances['stu']

        env = {'now': Datetime._from_datetime(dt.today())}

        self.master_candidates.vote_no_confidence(signer='stu', address='raghu', environment=env)

        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.master_candidates.vote_no_confidence(signer='stu', address='raghu', environment=env)

        self.assertEqual(self.currency.balances['stu'], stu_bal - 2)
        self.assertEqual(self.master_candidates.no_confidence_votes.get()['raghu'], 2)

        self.assertEqual(self.currency.balances['blackhole'], 2)

        self.assertEqual(self.master_candidates.no_confidence_state['last_voted', 'stu'], env['now'])

    def test_last_masternode_returns_none_if_no_candidates(self):
        self.assertIsNone(self.master_candidates.last_masternode())

    def test_last_masternode_returns_none_if_no_votes(self):
        self.assertEqual(self.master_candidates.last_masternode(), None)  # Joe is the current top spot

    def test_relinquish_fails_if_not_in_masternodes(self):
        with self.assertRaises(AssertionError):
            self.master_candidates.relinquish(signer='joebob')

    def test_relinquish_adds_ctx_signer_if_in_masternodes(self):
        self.master_candidates.relinquish(signer='raghu')

        self.assertIn('raghu', self.master_candidates.to_be_relinquished.get())

    def test_last_masternode_returns_relinquished_if_there_is_one_to_be_relinquished(self):
        self.master_candidates.relinquish(signer='raghu')

        self.assertEqual(self.master_candidates.last_masternode(), 'raghu')

    def test_last_masternode_returns_first_in_relinquished_if_multiple_are_to_be_relinquished(self):
        self.master_candidates.relinquish(signer='raghu')
        self.master_candidates.relinquish(signer='stux')

        self.assertEqual(self.master_candidates.last_masternode(), 'raghu')

    def test_last_masternode_returns_masternode_with_most_votes_if_none_in_relinquished(self):
        self.currency.approve(signer='stu', amount=10_000, to='master_candidates')  # Stu approves spending to vote
        env = {'now': Datetime._from_datetime(dt.today())}
        self.master_candidates.vote_no_confidence(signer='stu', address='raghu', environment=env)  # Stu votes for Bob

        self.assertEqual(self.master_candidates.last_masternode(), 'raghu')  # bob is the current top spot

    def test_last_masternode_returns_first_in_if_tie(self):
        self.currency.approve(signer='stu', amount=10_000, to='master_candidates')

        env = {'now': Datetime._from_datetime(dt.today())}

        self.master_candidates.vote_no_confidence(signer='stu', address='stux', environment=env)

        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.master_candidates.vote_no_confidence(signer='stu', address='raghu', environment=env)

        self.assertEqual(self.master_candidates.last_masternode(), 'stux')

    def test_last_masternode_returns_least_popular_if_multiple_votes(self):
        self.currency.approve(signer='stu', amount=10_000, to='master_candidates')

        env = {'now': Datetime._from_datetime(dt.today())}
        self.master_candidates.vote_no_confidence(signer='stu', address='stux', environment=env)

        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}
        self.master_candidates.vote_no_confidence(signer='stu', address='raghu', environment=env)

        env = {'now': Datetime._from_datetime(dt.today() + td(days=14))}
        self.master_candidates.vote_no_confidence(signer='stu', address='stux', environment=env)

        self.assertEqual(self.master_candidates.last_masternode(), 'stux')

    def test_pop_last_fails_if_not_masternodes_contract(self):
        with self.assertRaises(AssertionError):
            self.master_candidates.pop_last()

    def test_pop_last_doesnt_fail_if_masternodes_contract(self):
        self.master_candidates.pop_last(signer='masternodes')

    def test_pop_last_deletes_stux_if_is_last_masternode_and_no_relinquished(self):
        self.currency.approve(signer='stu', amount=10_000, to='master_candidates')

        env = {'now': Datetime._from_datetime(dt.today())}
        self.master_candidates.vote_no_confidence(signer='stu', address='stux', environment=env)

        self.assertIsNotNone(self.master_candidates.no_confidence_votes.get().get('stux'))
        self.master_candidates.pop_last(signer='masternodes')
        self.assertIsNone(self.master_candidates.no_confidence_votes.get().get('stux'))

    def test_pop_last_deletes_raghu_if_stux_voted_but_raghu_relinquished(self):
        self.currency.approve(signer='stu', amount=10_000, to='master_candidates')

        env = {'now': Datetime._from_datetime(dt.today())}
        self.master_candidates.vote_no_confidence(signer='stu', address='stux', environment=env)

        self.master_candidates.relinquish(signer='raghu')

        self.assertIsNotNone(self.master_candidates.no_confidence_votes.get().get('stux'))
        self.assertIn('raghu', self.master_candidates.to_be_relinquished.get())

        self.master_candidates.pop_last(signer='masternodes')

        self.assertNotIn('raghu', self.master_candidates.to_be_relinquished.get())
        self.assertIsNotNone(self.master_candidates.no_confidence_votes.get().get('stux'))

    def test_pop_last_deletes_raghu_from_no_confidence_hash_if_relinquished(self):
        self.currency.approve(signer='stu', amount=10_000, to='master_candidates')

        env = {'now': Datetime._from_datetime(dt.today())}
        self.master_candidates.vote_no_confidence(signer='stu', address='raghu', environment=env)

        self.master_candidates.relinquish(signer='raghu')

        self.assertIsNotNone(self.master_candidates.no_confidence_votes.get().get('raghu'))
        self.assertIn('raghu', self.master_candidates.to_be_relinquished.get())

        self.master_candidates.pop_last(signer='masternodes')

        self.assertNotIn('raghu', self.master_candidates.to_be_relinquished.get())
        self.assertIsNone(self.master_candidates.no_confidence_votes.get().get('raghu'))

    def test_no_confidence_pop_last_prevents_unregistering(self):
        # Give Raghu money
        self.currency.transfer(signer='stu', amount=100_000, to='raghu')

        # Raghu Allows Spending
        self.currency.approve(signer='raghu', amount=100_000, to='master_candidates')

        self.master_candidates.register(signer='raghu')

        self.currency.approve(signer='stu', amount=10_000, to='master_candidates')

        self.master_candidates.vote_no_confidence(signer='stu', address='raghu')

        self.master_candidates.pop_last(signer='masternodes')

        self.assertFalse(self.master_candidates.candidate_state['registered', 'raghu'])

        with self.assertRaises(AssertionError):
            self.master_candidates.unregister(signer='raghu')

    def test_relinquish_pop_last_allows_unregistering(self):
        # Give Raghu money
        self.currency.transfer(signer='stu', amount=100_000, to='raghu')

        # Raghu Allows Spending
        self.currency.approve(signer='raghu', amount=100_000, to='master_candidates')

        self.master_candidates.register(signer='raghu')

        self.currency.approve(signer='stu', amount=10_000, to='master_candidates')

        self.master_candidates.vote_no_confidence(signer='stu', address='raghu')
        self.master_candidates.relinquish(signer='raghu')
        self.master_candidates.pop_last(signer='masternodes')

        self.assertTrue(self.master_candidates.candidate_state['registered', 'raghu'])
        self.masternodes.quick_write('S', 'masternodes', ['stu'])
        self.master_candidates.unregister(signer='raghu')

    def test_force_removal_fails_if_not_masternodes(self):
        with self.assertRaises(AssertionError):
            self.master_candidates.force_removal(address='stux')

    def test_force_removal_unregisters_address(self):
        # Give Raghu money
        self.currency.transfer(signer='stu', amount=100_000, to='stux')

        # Raghu Allows Spending
        self.currency.approve(signer='stux', amount=100_000, to='master_candidates')

        self.master_candidates.register(signer='stux')
        self.master_candidates.force_removal(signer='masternodes', address='stux')
        self.assertFalse(self.master_candidates.candidate_state['registered', 'stux'])

