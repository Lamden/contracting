v = Variable()

@export
def get():
    return v.get()

@seneca_construct
def seed():
    v.set(42)
