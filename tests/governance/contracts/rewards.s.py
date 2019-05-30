import currency
import masternodes
import delegates

shares = Hash()

EPOCH_LENGTH = 100_000
EPOCH = block_num // EPOCH_LENGTH

@export
def withdraw(epoch):
    assert epoch > EPOCH, 'Current reward epoch is not over yet!'

    mn_list = masternodes.get_all()
    del_list = delegates.get_all()

    assert ctx.caller in mn_list or ctx.caller in del_list, 'Only delegates and masternodes can withdraw a reward'

    # This is the first time someone is trying to withdraw from this epoch
    if not shares[epoch, 'is_closed']:
        assert isinstance(del_list, list)

        participants = len(mn_list) + len(del_list)
        shares[epoch, 'amount'] = shares[epoch, 'balance'] / participants
        shares[epoch, 'is_closed'] = True

    # Make sure this person has not redeemed yet
    if not shares[epoch, 'redeemed', ctx.caller]:
        currency.transfer(ctx.caller, shares[epoch, 'amount'])
        shares[epoch, 'redeemed', ctx.caller] = True
