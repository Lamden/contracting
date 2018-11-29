from seneca.libs.math import random

cards = [1, 2, 3, 4, 5, 6, 7, 8]


def shuffle_cards():
    random.shuffle(cards)
    return cards


def random_number(k):
    return random.randrange(k)
