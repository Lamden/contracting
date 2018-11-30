import random
from seneca.engine.book_keeper import BookKeeper

'''
    This module wraps and exposes the Python stdlib random functions
    that can be made deterministic with a random seed and return fixed
    point precision where possible. This allows some psuedorandom
    behavior when it is nice to have, but with the caveat that it's
    based on environmental constants such as the last block hash and
    public information such as the sender's address to seed the random
    state.
'''


class Seeded:
    s = False


def seed(d):
    try:
        seed = BookKeeper.get_info().get('last_block_hash')
    except Exception as e:
        seed = b'0'

    if isinstance(seed, str):
        seed.encode()

    assert isinstance(d, bytes), 'Must provide bytes to seed.'

    random.seed(seed + d)
    Seeded.s = True


def require_seed(f):
    def wrapper():
        assert Seeded.s, 'Random state not seeded. Call seed().'
        f()
    return wrapper


@require_seed
def getrandbits(k):
    return random.getrandbits(k)


@require_seed
def shuffle(l):
    random.shuffle(l)


@require_seed
def randrange(k):
    return random.randrange(k)


@require_seed
def randint(a, b):
    return random.randint(a, b)


@require_seed
def choice(l):
    return random.choice(l)


@require_seed
def choices(l, k):
    return random.choices(l, k=k)