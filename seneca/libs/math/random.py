import random
from seneca.engine.book_keeper import BookKeeper

try:
    seed = BookKeeper.get_info().get('last_block_hash')
except Exception as e:
    seed = b'0'

random.seed(seed)


def getrandbits(k):
    random.seed(seed)
    return random.getrandbits(k)


def shuffle(l):
    random.shuffle(l)


def randrange(k):
    random.seed(seed)
    return random.randrange(k)


def randint(a, b):
    random.seed(seed)