cost = Variable()
votes = Hash()

election_frequency = timedelta.WEEKS * 1
election_duration = timedelta.WEEKS * 1

in_election = Variable()

@construct
def seed():
    cost.set(1)


