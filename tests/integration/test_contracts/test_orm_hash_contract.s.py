h = Hash()

@export
def set_h(k, v):
    h.set(k, v)

@export
def get_h(k):
    return h.get(k)
