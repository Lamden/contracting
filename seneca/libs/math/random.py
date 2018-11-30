import random
from seneca.engine.book_keeper import BookKeeper


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
