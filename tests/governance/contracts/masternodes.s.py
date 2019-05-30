import stake

EPOCH_LENGTH = 100_000
EPOCH = block_num // EPOCH_LENGTH

masternodes = Hash()

current_electorate = Variable()
votes = Hash()
has_voted = Hash()

@construct
def seed():
    masternodes[0] = [
        'stu',
        'raghu',
        'tejas'
    ]

    current_electorate.set(0) # The number of the


@export
def get_for_epoch(e):
    return masternodes[e]

@export
def vote(account):
    # Make sure user can actually vote for who they want to
    assert stake.is_staked(ctx.caller), 'You cannot vote if you are not staked!'
    assert stake.is_staked(account), 'You cannot vote for someone unstaked!'
    assert not has_voted[EPOCH, ctx.caller], 'You cannot vote twice!'

    # Add to the current epoch's vote and prevent them from double voting
    votes[EPOCH, account] += 1
    has_voted[EPOCH, ctx.caller] = True

    # Tally the votes if we are in a new Epoch beyond the current electorate
    e = current_electorate.get()
    if EPOCH > e:
        tally()

@export
def tally():
    pass