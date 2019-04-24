v = Variable()

@seneca_construct
def seed():
    v.set([1, 2, 3, 4, 5, 6, 7, 8])

@seneca_export
def get_some():
    return v.get()[0:4]
