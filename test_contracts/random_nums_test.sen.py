from seneca.libs.math import random

random.seed()

cards = [1, 2, 3, 4, 5, 6, 7, 8]

@export
def shuffle_cards(**kwargs):
    random.shuffle(cards)
    return cards

@export
def random_number(k):
    return random.randrange(k)

@export
def random_number_2(k):
    # adjust the random state by calling another random function
    shuffle_cards()
    return random.randrange(k)

@export
def random_bits(k):
    shuffle_cards()
    shuffle_cards()
    shuffle_cards()
    return random.getrandbits(k)