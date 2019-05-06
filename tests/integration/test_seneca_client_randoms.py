from unittest import TestCase
from contracting.client import ContractingClient


def random_contract():
    random.seed()

    cards = [1, 2, 3, 4, 5, 6, 7, 8]

    cardinal_values = ['A', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    suits = ['S', 'C', 'H', 'D']

    cities = ['Cleveland', 'Detroit', 'Chicago', 'New York', 'San Francisco']

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

    @export
    def int_in_range(a, b):
        shuffle_cards()
        shuffle_cards()
        return random.randint(a, b)

    @export
    def deal_card():
        random.shuffle(cardinal_values)
        random.shuffle(cardinal_values)
        random.shuffle(cardinal_values)

        random.shuffle(suits)
        random.shuffle(suits)
        random.shuffle(suits)

        c = ''
        c += random.choice(cardinal_values)
        c += random.choice(suits)

        return c

    @export
    def pick_cities(k):
        return random.choices(cities, k)


class TestRandomsContract(TestCase):
    def setUp(self):
        self.c = ContractingClient(signer='stu')
        self.c.flush()
        self.c.submit(random_contract)

        self.random_contract = self.c.get_contract('random_contract')

    def tearDown(self):
        self.c.flush()

    def test_basic_shuffle(self):
        cards_1 = self.random_contract.shuffle_cards()
        cards_2 = self.random_contract.shuffle_cards()

        self.assertEqual(cards_1, cards_2)

    def test_random_num_one_vs_two(self):
        k = self.random_contract.random_number(k=1000)
        k2 = self.random_contract.random_number_2(k=1000)

        self.assertNotEqual(k, k2)

        self.assertEqual(k, 784)
        self.assertEqual(k2, 161)

    def test_random_getrandbits(self):
        b = self.random_contract.random_bits(k=20)
        self.assertEqual(b, 178715)

    def test_random_range_int(self):
        a = self.random_contract.int_in_range(a=100, b=50000)

        self.assertEqual(a, 37565)

    def test_random_choice(self):
        cities = self.random_contract.pick_cities(k=2)
        self.assertListEqual(cities, ['New York', 'Cleveland'])