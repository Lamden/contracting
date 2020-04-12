test_hash = Hash()

@export
def call_private():
    return private()

def private():
    return 'abc'

@export
def set(k: str, v: int):
    test_hash[k] = v

@export
def set_multi(k: str, k2: str, k3: str, v: int):
    test_hash[k, k2, k3] = v