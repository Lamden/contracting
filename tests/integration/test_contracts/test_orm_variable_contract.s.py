v = Variable()

@seneca_export
def set_v(i):
    v.set(i)

@seneca_export
def get_v():
    return v.get()
