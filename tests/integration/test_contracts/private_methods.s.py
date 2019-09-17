test_hash = Hash()

@export
def call_private():
    return private()

def private():
    return 'abc'

@export
def set(k, v):
    test_hash[k] = v

@export
def set_multi(k, k2, k3, v):
    test_hash[k, k2, k3] = v