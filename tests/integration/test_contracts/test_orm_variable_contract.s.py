v = Variable()

@construct
def seed():
    print('howdy jeff')

@construct
def seed2():
    print('hahaha')

@export
def set_v(i):
    v.set(i)

@export
def get_v():
    return v.get()

def shhhh():
    print('dont call this')
