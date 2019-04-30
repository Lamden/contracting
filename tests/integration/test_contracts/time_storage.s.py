time = Variable()

@seneca_construct
def seed():
    time.set(datetime(2019, 1, 1))

@export
def get():
    return time.get()
