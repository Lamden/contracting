from unittest import TestCase
from seneca.engine.datatypes import *


class TestDatatypes(TestCase):
    def setUp(self):
        self.r = redis.StrictRedis(host='localhost',
                                   port=6379,
                                   db=0)

    def test_type_mappings(self):
        self.assertTrue(type_to_string[str] == 'str')
        self.assertTrue(type_to_string[int] == 'int')
        self.assertTrue(type_to_string[bool] == 'bool')

        self.assertTrue(string_to_type['str'] == str)
        self.assertTrue(string_to_type['int'] == int)
        self.assertTrue(string_to_type['bool'] == bool)

    def test_parse_representation_map(self):
        repr_str = ':map:test:int:str'
        m = parse_representation(repr_str)

        self.assertTrue(type(m) == HMap)
        self.assertTrue(m.key_type == int)
        self.assertTrue(m.value_type == str)

    def test_placeholder(self):
        p = Placeholder(placeholder_type=HMap)

        self.assertTrue(p.key_type == str)
        self.assertTrue(p.value_type == int)
        self.assertTrue(p.placeholder_type == HMap)

        good_repr_str = ':map:some_map:str:int'
        good_map = parse_representation(good_repr_str)

        self.assertTrue(p.valid(good_map))

        bad_repr_str = ':map:some_other_map:int:str'
        bad_map = parse_representation(bad_repr_str)

        self.assertFalse(p.valid(bad_map))

    def test_robject_encoding_variable(self):
        r = RObject()

        with self.assertRaises(AssertionError):
            r.encode_value('s')

        v = r.encode_value(1)

        self.assertTrue(type(v), bytes)
        self.assertTrue(v.decode(), '1')

    def test_robject_encoding_placeholder(self):
        p = Placeholder(placeholder_type=HMap)
        r = RObject(value_type=p)

        repr_str = ':map:howdy:str:int'
        _map = parse_representation(repr_str)

        v = r.encode_value(_map)

        self.assertTrue(type(v), bytes)
        self.assertTrue(v.decode(), repr_str)

    def test_robject_decoding_variable(self):
        r = RObject()
        self.assertTrue(r.decode_value(b'1'), 1)
        self.assertTrue(r.decode_value(b'"s"'), 's')
        self.assertTrue(r.decode_value(b'[1, 2, 3]'), [1, 2, 3])

        repr_str = b':map:howdy:str:int'
        decoded_map = r.decode_value(repr_str)

        self.assertTrue(type(decoded_map), HMap)
        self.assertTrue(decoded_map.key_type, str)
        self.assertTrue(decoded_map.value_type, int)
        self.assertTrue(decoded_map.prefix, 'howdy')