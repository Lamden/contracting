h = Hash()

@seneca_export
def set_h(k, v):
    h.set(k, v)

@seneca_export
def get_h(k):
    return h.get(k)
