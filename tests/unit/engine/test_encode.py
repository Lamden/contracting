from unittest import TestCase
from seneca.storage.encoder import encode, decode
from decimal import Decimal as dec


class TestEncode(TestCase):
    def test_int_to_bytes(self):
        i = 1000
        b = b'i1000'

        self.assertEqual(encode(i), b)

    def test_str_to_bytes(self):
        s = 'hello'
        b = b'shello'

        self.assertEqual(encode(s), b)

    def test_dec_to_bytes(self):
        d = dec('1.098409840984')
        b = b'd1.098409840984'

        self.assertEqual(encode(d), b)

    def test_bytes_to_bytes(self):
        _b = b'bytes'
        b = b'bbytes'

        self.assertEqual(encode(_b), b)

    def test_decode_bytes_to_int(self):
        b = b'i1234'
        i = 1234

        self.assertEqual(decode(b), i)

    def test_decode_bytes_to_str(self):
        b = b'showdy'
        s = 'howdy'

        self.assertEqual(decode(b), s)

    def test_decode_bytes_to_dec(self):
        b = b'd0.0044997618965276'
        d = dec('0.0044997618965276')

        self.assertEqual(decode(b), d)

    def test_decode_bytes_to_bytes(self):
        b = b'buggg'
        bb = b'uggg'

        self.assertEqual(decode(b), bb)

    def test_decode_failure(self):
        b = b'xwow'

        self.assertIsNone(decode(b))