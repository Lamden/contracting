from test_contracts.good import one_you_can_export as good
from test_contracts.okay import one_you_can_export as okay

@export
def good_call():
    good()
    okay()

@export
def reasonable_call():
    good()

@export
def do_that_thing():
    return 'sender: {}, author: {}'.format(rt['sender'], rt['author'])

@export
def test_global_namespace():
    print('sender: {}, author: {}'.format(rt['sender'], rt['author']))
    print("sbb_idx: {}".format(sbb_idx))
    print("ALL GLOBALS: {}".format(globals()))

def secret_call():
    okay()
