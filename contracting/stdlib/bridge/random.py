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

import random
from types import ModuleType
from ...execution.runtime import rt

block_height = rt.env.get('block_height') or '0'
block_hash = rt.env.get('block_hash') or '0'


class Seeded:
    s = False


def seed():
    random.seed(block_height + block_hash)
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


# Construct module for exposure in the contract runtime
random_module = ModuleType('random')
random_module.seed = seed
random_module.shuffle = shuffle
random_module.getrandbits = getrandbits
random_module.randrange = randrange
random_module.randint = randint
random_module.choice = choice
random_module.choices = choices

# Add it to the export object and it's good to go
exports = {
    'random': random_module
}


