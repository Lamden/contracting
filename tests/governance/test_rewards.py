from unittest import TestCase
from contracting.client import ContractingClient
from contracting.stdlib.bridge.time import WEEKS, DAYS, Datetime
from datetime import datetime as dt, timedelta as td


def rewards():
    value = Variable()
    current_votes = Hash(default_value=0)
    has_voted = Hash()

    last_election = Variable()
    election_start = Variable()

    election_length = datetime.DAYS * 1
    election_interval = datetime.WEEKS * 1

    @construct
    def seed():
        value.set([0.5, 0.5, 0, 0])
        last_election.set(now)
        election_start.set(None)

    @export
    def current_value():
        return value.get()

    @export
    def vote(vk, obj):
        if election_start.get() is not None:
            tally_vote(vk, obj)

            # If it has been over a day since the election started... End the election
            if now - election_start.get() >= election_length:
                # Calculate ratio of votes
                masternode_votes = current_votes['masternodes'] or 1
                delegate_votes = current_votes['delegates'] or 1
                blackhole_votes = current_votes['blackhole'] or 1
                foundation_votes = current_votes['foundation'] or 1

                total_votes = masternode_votes + delegate_votes + blackhole_votes + foundation_votes

                # Do the same for each party before dividing
                mn = masternode_votes / total_votes
                dl = delegate_votes / total_votes
                bh = blackhole_votes / total_votes
                fd = foundation_votes / total_votes

                # Set the new value
                value.set([mn, dl, bh, fd])

                # Reset everything
                election_start.set(None)
                last_election.set(now)
                current_votes.clear()
                has_voted.clear()

        # If its been 1 week since the last election ended... Start the election
        elif now - last_election.get() > election_interval:
            # Set start to now
            election_start.set(now)
            current_votes.clear()
            tally_vote(vk, obj)

    def tally_vote(vk, obj):
        assert vote_is_valid(obj), 'Invalid vote object passed!'
        assert has_voted[vk] is None, 'VK has already voted!'

        has_voted[vk] = True

        a, b, c, d = obj

        current_votes['masternodes'] += a
        current_votes['delegates'] += b
        current_votes['blackhole'] += c
        current_votes['foundation'] += d

    def vote_is_valid(obj):
        if type(obj) != list:
            return False

        if len(obj) != 4:
            return False

        s = 0
        for o in obj:
            if type(o) != int:
                return False
            if o < 0:
                return False
            s += o

        if s != 100:
            return False

        return True


class TestRewards(TestCase):
    def setUp(self):
        self.c = ContractingClient()
        self.c.flush()

        with open('./contracts/election_house.s.py') as f:
            contract = f.read()

        self.c.submit(contract, name='election_house')
        self.c.submit(rewards, owner='election_house')
        self.c.raw_driver.commit()

        self.election_house = self.c.get_contract('election_house')
        self.rewards = self.c.get_contract('rewards')

        self.election_house.register_policy(contract='rewards')

    def tearDown(self):
        self.c.flush()

    def test_vote_not_list_fails(self):
        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        with self.assertRaises(AssertionError):
            self.election_house.vote(policy='rewards', value=False, environment=env)

    def test_vote_list_not_ints_fails(self):
        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        with self.assertRaises(AssertionError):
            self.election_house.vote(policy='rewards', value=['a', 'b', 'c', 'd'], environment=env)

    def test_vote_list_not_4_elements_fails(self):
        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        with self.assertRaises(AssertionError):
            self.election_house.vote(policy='rewards', value=[1, 2, 3], environment=env)

    def test_vote_list_negatives_fails(self):
        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        with self.assertRaises(AssertionError):
            self.election_house.vote(policy='rewards', value=[1, 2, 3, -1], environment=env)

    def test_vote_list_sum_not_100_fails(self):
        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        with self.assertRaises(AssertionError):
            self.election_house.vote(policy='rewards', value=[99, 0, 0, 0], environment=env)

    def test_vote_list_sum_100_succeeds(self):
        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.election_house.vote(policy='rewards', value=[25, 25, 25, 25], environment=env)
        self.assertEqual(self.rewards.current_votes['masternodes'], 25)
        self.assertEqual(self.rewards.current_votes['delegates'], 25)
        self.assertEqual(self.rewards.current_votes['blackhole'], 25)
        self.assertEqual(self.rewards.current_votes['foundation'], 25)

    def test_vote_twice_fails(self):
        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.election_house.vote(policy='rewards', value=[25, 25, 25, 25], environment=env)
        with self.assertRaises(AssertionError):
            self.election_house.vote(policy='rewards', value=[25, 25, 25, 25], environment=env)

    def test_vote_finished_returns_average_sum(self):
        env = {'now': Datetime._from_datetime(dt.today() + td(days=7))}

        self.election_house.vote(policy='rewards', value=[25, 25, 25, 25], environment=env, signer='v1')
        self.election_house.vote(policy='rewards', value=[25, 0, 50, 25], environment=env, signer='v2')
        self.election_house.vote(policy='rewards', value=[25, 0, 0, 75], environment=env, signer='v3')

        env = {'now': Datetime._from_datetime(dt.today() + td(days=8))}

        self.election_house.vote(policy='rewards', value=[100, 0, 0, 0], environment=env, signer='v4')

        # Expected [176, 26, 76, 126] / 404 = [0.4375, 0.0625, 0.1875, 0.3125]

        self.assertEqual(self.election_house.current_value_for_policy(policy='rewards'), [0.4375, 0.0625, 0.1875, 0.3125])