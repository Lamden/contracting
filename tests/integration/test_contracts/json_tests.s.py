v = Variable()

@construct
def seed():
    v.set([1, 2, 3, 4, 5, 6, 7, 8])

@export
def get_some():
    return v.get()[0:4]
