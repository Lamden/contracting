@export
def t_sha3(s):
    return hashlib.sha3(s)

@export
def t_sha256(s):
    return hashlib.sha256(s)
