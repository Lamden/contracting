time = Variable()

@construct
def seed():
    time.set(datetime.datetime(2019, 1, 1))

@export
def get():
    return time.get()
