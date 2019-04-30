from unittest import TestCase
from contracting.db.encoder import encode, decode
from decimal import Decimal as dec
from contracting.stdlib.bridge.time import Datetime
from datetime import datetime

class TestEncode(TestCase):
    def test_int_to_bytes(self):
        i = 1000
        b = '1000'

        self.assertEqual(encode(i), b)

    def test_str_to_bytes(self):
        s = 'hello'
        b = '"hello"'

        self.assertEqual(encode(s), b)

    def test_dec_to_bytes(self):
        d = 1.098409840984
        b = '1.098409840984'

        self.assertEqual(encode(d), b)

    def test_decode_bytes_to_int(self):
        b = '1234'
        i = 1234

        self.assertEqual(decode(b), i)

    def test_decode_bytes_to_str(self):
        b = '"howdy"'
        s = 'howdy'

        self.assertEqual(decode(b), s)

    def test_decode_bytes_to_dec(self):
        b = '0.0044997618965276'
        d = dec('0.0044997618965276')

        self.assertEqual(decode(b), d)

    def test_decode_failure(self):
        b = b'xwow'

        self.assertIsNone(decode(b))

    def test_date_encode(self):
        d = Datetime(2019, 1, 1)

        _d = encode(d)

        self.assertEqual(_d, '{"__time__": [2019, 1, 1, 0, 0, 0, 0]}')

    def test_date_decode(self):
        _d = '{"__time__": [2019, 1, 1, 0, 0, 0, 0]}'

        d = decode(_d)

        self.assertEqual(Datetime(2019, 1, 1), d)
