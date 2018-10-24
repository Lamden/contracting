from seneca.test_contracts.good import one_you_can_export as good
from seneca.test_contracts.okay import one_you_can_export as okay
# import seneca.libs.runtime as rt

@export
def good_call():
    good()
    okay()

@export
def reasonable_call():
    good()

@export
def do_that_thing():
    print("do_that_thing called")
    print("all globals: {}".format(globals()))
    print("sender: {}".format(rt.sender))
    print("author: {}".format(rt.author))
    print("do_that_thing over")

def secret_call():
    okay()
