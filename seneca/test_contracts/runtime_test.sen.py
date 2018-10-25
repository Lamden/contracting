from seneca.libs.datatypes import *


balances = hmap('balances', str, int)


@export
def test_global_namespace():
    print('sender: {}, author: {}'.format(rt.sender, rt.author))
    print("sbb_idx: {}".format(sbb_idx))
    print("ALL GLOBALS: {}".format(globals()))


