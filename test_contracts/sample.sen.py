from test_contracts.good import one_you_can_export as good_export, assert_export_to_sample
from test_contracts.okay import one_you_can_export as okay_export

@export
def good_call():
    good_export()
    okay_export()

@export
def assert_call():
    assert_export_to_sample()
    assert rt['contract'] == 'sample' and rt['sender'] == '__main__', 'Contract not maintained'

@export
def reasonable_call():
    good_export()

@export
def do_that_thing():
    return 'sender: {}, author: {}'.format(rt['sender'], rt['author'])

@export
def test_global_namespace():
    print('sender: {}, author: {}'.format(rt['sender'], rt['author']))
    print("sbb_idx: {}".format(sbb_idx))

def secret_call():
    okay_export()
