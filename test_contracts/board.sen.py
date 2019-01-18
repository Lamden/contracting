from seneca.libs.datatypes import hmap
from seneca.contracts.tau import transfer, get_balance, spend_custodial

owners = hmap('owners', str, str)
prices = hmap('prices', str, int)
colors = hmap('colors', str, str)

MAX_X = 250
MAX_Y = 250
board_owner = 'falcon'

def coor_str(x, y):
    return '{},{}'.format(x, y)

def owner_of_pixel(x, y):
    return owners[coor_str(x, y)]

@export
def price_of_pixel(x, y):
    return prices[coor_str(x, y)]

@export
def buy_pixel(x, y, r, g, b, new_price=0):


    assert new_price >= 0, 'New price must be a positive amount'

    x, y, r, g, b = [int(i) for i in [x, y, r, g, b]]

    assert x >= 0 and x < MAX_X and \
           y >= 0 and y < MAX_Y and \
           r >= 0 and r < 256 and \
           g >= 0 and g < 256 and \
           b >= 0 and b < 256, "Invalid pixel selection"

    price = price_of_pixel(x, y)

    assert get_balance(rt['sender']) >= price, 'Not enough funds to buy the pixel'

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
    assert rt['sender'] == owner, 'Only owner of the pixel can view its price'

    x = int(x)
    y = int(y)

    new_price = int(new_price)
    prices[coor_str(x, y)] = new_price

@export
def color_pixel(x, y, r, g, b):
    owner = owner_of_pixel(x, y)
    assert rt['sender'] == owner, 'Only owner of the pixel can change the pixel color'

    r = int(r)
    g = int(g)
    b = int(b)

    colors[coor_str(x, y)] = '{},{},{}'.format(r, g, b)
