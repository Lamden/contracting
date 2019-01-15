from seneca.libs.datatypes import hmap
from seneca.contracts.tau import transfer, get_balance, spend_custodial

board_owner = 'falcon'

owners = hmap('owners', str, str)
prices = hmap('prices', str, int)
colors = hmap('colors', str, str)

max_x = 250
max_y = 250

def coor_str(x, y):
    return '{},{}'.format(x, y)

def owner_of_pixel(x, y):
    return owners[coor_str(x, y)]

@export
def price_of_pixel(x, y):
    return prices[coor_str(x, y)]

@export
def buy_pixel(x, y, r, g, b, new_price=0):


    assert new_price >= 0

    x, y, r, g, b = [int(i) for i in [x, y, r, g, b]]

    assert x >= 0 and x < max_x
    assert y >= 0 and y < max_y
    assert r >= 0 and r < 256
    assert g >= 0 and g < 256
    assert b >= 0 and b < 256

    price = price_of_pixel(x, y)

    assert get_balance(rt['sender']) >= price

    owner = owner_of_pixel(x, y)

    # Set the owner to the default board owner if it is not set
    if owner == '':
        owner = board_owner

    spend_custodial(rt['sender'], price, owner)

    owners[coor_str(x, y)] = rt['sender']
    prices[coor_str(x, y)] = new_price if new_price > 0 else price
    colors[coor_str(x, y)] = '{},{},{}'.format(r, g, b)

@export
def price_pixel(x, y, new_price):
    owner = owner_of_pixel(x, y)
    assert rt['sender'] == owner

    x = int(x)
    y = int(y)

    new_price = int(new_price)
    prices[coor_str(x, y)] = new_price

@export
def color_pixel(x, y, r, g, b):
    owner = owner_of_pixel(x, y)
    assert rt['sender'] == owner

    r = int(r)
    g = int(g)
    b = int(b)

    colors[coor_str(x, y)] = '{},{},{}'.format(r, g, b)
