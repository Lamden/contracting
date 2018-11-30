import random
from seneca.engine.book_keeper import BookKeeper

'''
    This module wraps and exposes the Python stdlib random functions that can be made deterministic with a random seed 
    and return fixed point precision where possible. This allows some psuedorandom behavior when it is nice to have, but
    with the caveat that it's based on environmental constants such as the last block hash and public information such
    as the sender's address to seed the random state so it's not *really* random.
    
    It's most likely 'random enough' for most cases, but people can always theoretically reproduce the seed and try to
    front-run a smart contract by testing the seeded randoms for a preferable outcome and submitting a transaction
    before the next block is minted. While this is extremely unlikely and hard to pull off, it's a valid hole in the
    security and needs to be accepted as a flaw when using random numbers on a reproducible transaction log such as a 
    blockchain.
'''


class Seeded:
    s = False


def seed(d=None):
    try:
        seed = BookKeeper.get_info().get('last_block_hash')
    except Exception as e:
        seed = b'0'

    if isinstance(seed, str):
        seed.encode()

    assert isinstance(d, bytes) or d is None, 'Must provide bytes to seed.'

    if d is not None:
        seed += d

    random.seed(seed)
    Seeded.s = True


def getrandbits(k):
    assert Seeded.s, 'Random state not seeded. Call seed().'
    return random.getrandbits(k)


def shuffle(l):
    assert Seeded.s, 'Random state not seeded. Call seed().'
    random.shuffle(l)


def randrange(k):
    assert Seeded.s, 'Random state not seeded. Call seed().'
    return random.randrange(k)


def randint(a, b):
    assert Seeded.s, 'Random state not seeded. Call seed().'
    return random.randint(a, b)


def choice(l):
    assert Seeded.s, 'Random state not seeded. Call seed().'
    return random.choice(l)


def choices(l, k):
    assert Seeded.s, 'Random state not seeded. Call seed().'
    return random.choices(l, k=k)
