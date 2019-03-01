from seneca.libs.storage.datatypes import Hash, Key, Table, SchemaArgs

michelin_stars = Key()
restaurant_name = Key()
address = Key()
menu = Hash('menu')
cart = Table('cart', {
    'customer_id': SchemaArgs(str, primary_key=True),
    'item': SchemaArgs(str, required=True, indexed=True)
})

@seed
def start_restaurant():
    michelin_stars = 0
    restaurant_name = 'Alpha Star Cuisine'
    address = '1337 Lowe Lane'
    menu['Vegan Ramen'] = 13
    menu['Rainbow Roll'] = 12.5

@export
def add_item(item_name):
    cart.add_row(rt['sender'], item_name)

@export
def show_cart():
    cart.find(field='customer_id', exactly=rt['sender'])

@export
def remove_item(item_idx):
    cart