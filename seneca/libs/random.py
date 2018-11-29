import random
from seneca.engine.book_keeper import BookKeeper

try:
    seed = BookKeeper.get_info()
except:
    seed = b'0'


def random_bits(k):
    random.seed(seed)
    return random.getrandbits(k)
