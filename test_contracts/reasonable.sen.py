@export
def reasonable_call():
    return 'sender: {}, contract: {}'.format(__sender__, __contract__)

@export
def call_with_args(required, not_required="gg"):
    return required, not_required
