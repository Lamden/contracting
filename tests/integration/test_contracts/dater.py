#import datetime

v = Variable()

@export
def replicate(d: datetime.datetime):
    assert d > now, 'D IS NOT LARGER THAN NOW'
    v.set(d)

@export
def subtract(d1: datetime.datetime, d2: datetime.datetime):
    return d1 - d2
