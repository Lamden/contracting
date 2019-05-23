votable = Variable()

votes = Hash()

in_election = Variable()
last_election_end_time = Variable() # Datetime. now - last_election_end_time to determine if a new election can start
election_interval = Variable() # Time delta. How often elections can be run
voting_period = Variable() # Time delta. How long you can vote for
election_start_time = Variable()

@construct
def seed()
    votable.set(100)
    in_election.set(False)

@export
def get_votable():
    return votable.get()

@export
def vote(v):
    # Check to make sure that there is an election
    if is_currently_election():
        submit_vote(v)
        if election_should_end():
            tally_votes()
            reset_election_variables()
    else:
        # If there isn't, it might be time for a new one, so start it if so.
        # You can then submit your vote as well.
        if election_can_start():
            start_election()
            submit_vote(v)

def is_currently_election():
    if in_election.get():
        return True
    return False

def submit_vote(v):
    if votes[ctx.sender] is not None:
        votes[ctx.sender] = v

def election_should_end():
    if now - election_start_time.get() >= voting_period.get():
        return True
    return False

def median(vs):
    sorted_votes = sorted(vs)
    index = (len(sorted_votes) - 1) // 2

    if len(sorted_votes) % 2:
        return sorted_votes[index]
    else:
        return (sorted_votes[index] + sorted_votes[index + 1])/2

def tally_votes():
    result = median(votes.all())
    votable.set(result)

def reset_election_variables():
    last_election_end_time.set(now)
    in_election.set(False)
    del votes

def election_can_start():
    if now - last_election_end_time.get() > election_interval.get():
        return True
    return False

def start_election():
    election_start_time.set(now)
    in_election.set(True)