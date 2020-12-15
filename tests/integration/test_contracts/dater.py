v = Variable()

@export
def replicate(d: datetime.datetime):
    assert d > now, 'D IS NOT LARGER THAN NOW'
    v.set(d)

@export
def sniff_type(d: datetime.datetime):
    return type(d)
