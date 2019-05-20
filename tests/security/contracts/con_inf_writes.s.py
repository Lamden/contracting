hhash = Hash(default_value=0)

@construct
def seed():
    hashed_data = 'woohoo'
    while True:
        hashed_data = hashlib.sha3(hashed_data)
        hhash[hashed_data] = 'a'

@export
def dummy():
    return 0