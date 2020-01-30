import math

pi = Variable()

@construct
def seed():
    pi.set(math.pi)


@export
def get_pi():
    return pi.get()