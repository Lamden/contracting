from seneca.engine.datatypes import hmap, ranked, table, hlist

now = 12345 # unix timestamp


class Context:
    def __init__(self, sender=None, author=None):
        self.sender = sender
        self.author = author


rt = Context()

current_delegates = hlist('delegates', str)
votes = ranked('votes')
last_vote = hmap('last_vote', str, int)

defaults = hmap('defaults', str, None)
defaults.set('period_on', 10000)
defaults.set('period_off', 100000)
defaults.set('last_election', 0)
defaults.get('in_vote', False)
defaults.get('delegate_count', 63)


def vote_for_delegate(d):
    last_election = defaults.get('last_election')
    if last_vote.get(rt.sender) != last_election:
        last_vote.set(rt.sender, now)
        return votes.increment(d, 1)


def initiate_vote():
    # make sure we are not in a vote
    if not defaults.get('in_vote'):
        last_election = defaults.get('last_election')
        period_off = defaults.get('period_off')
        period_on = defaults.get('period_on')

        # make sure that enough time has passed to start a new vote
        if now > last_election + period_off:
            defaults.set('in_vote', True)

            # set the last election to a point in the future so that we can easily see if its time to end the vote
            defaults.set('last_election', now + period_on)
            #current_delegates.drop()


def end_vote():
    if defaults.get('in_vote'):
        last_election = defaults.get('last_election')

        if now > last_election:
            defaults.set('in_vote', False)
