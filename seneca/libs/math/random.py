import random
from seneca.engine.book_keeper import BookKeeper

try:
    seed = BookKeeper.get_info().get('last_block_hash')
except Exception as e:
    seed = b'0'


def getrandbits(k):
    random.seed(seed)
    return random.getrandbits(k)


def shuffle(l):
    random.seed(seed)
    random.shuffle(l)


def randrange(k):
    random.seed(seed)
    return random.randrange(k)


def randint(a, b):
    random.seed(seed)
    return 

l = [1, 2, 3, 4, 5, 6, 7, 8]
shuffle(l)

shuffle(l)

print(l)