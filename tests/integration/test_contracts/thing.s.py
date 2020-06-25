H = Hash()
V = Variable()

@construct
def seed():
    H['hello'] = 'there'
    H['something'] = 'else'
    V.set('hi')

@export
def nop():
    pass
