v = Variable()

@export
def replicate(d: datetime.datetime):
    assert d > now, 'D IS NOT LARGER THAN NOW'
    v.set(d)
