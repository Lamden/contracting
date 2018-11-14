@export
def reasonable_call():
    return 'sender: {}, contract: {}'.format(rt['sender'], rt['contract'])

@export
def call_with_args(required, not_required="gg"):
    return required, not_required
