from unittest import TestCase
from seneca.engine.datatypes import *

'''
test complex key types and value types
test more failure cases
'''

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

    def test_robject_check_key_type(self):
        r = RObject()
        with self.assertRaises(AssertionError):
            r.check_key_type(1)

        r.check_key_type('a')

    def test_hmap_set_get(self):
        m = HMap(prefix='howdy')
        m.set('stu', 100)

        s = m.get('stu')

        self.assertEqual(s, 100)

        with self.assertRaises(AssertionError):
            m.set('stu', 'stu')

        n = m.get('not_stu')
        self.assertEqual(n, None)

    def test_hmap_getitem_setitem(self):
        m = HMap(prefix='howdy2')
        m['stu'] = 1000000
        self.assertEqual(m['stu'], 1000000)

        with self.assertRaises(AssertionError):
            m['stu'] = 'stu'

        n = m['not_stu']
        self.assertEqual(n, None)

    def test_hmap_convenience_function(self):
        m = hmap()
        self.assertTrue(isinstance(m, Placeholder))

        m2 = hmap('howdy')
        self.assertTrue(isinstance(m2, HMap))

    def test_hlist_init_repr(self):
        l = HList(prefix='yo')
        self.assertEqual(l.rep(), ':list:yo:int:')
        self.assertEqual(l.len, None)
        self.assertEqual(l.p, 'yo:')

    def test_hlist_push_pop(self):
        l = HList(prefix='yo')
        l.push(123)

        with self.assertRaises(AssertionError):
            l.push('123')

        x = l.pop()

        self.assertEqual(x, 123)

    def test_hlist_get(self):
        l = HList(prefix='yo')
        l.push(123)
        l.push(567)

        x = l.get(1)
        y = l.get(0)

        self.assertEqual(x, 123)
        self.assertEqual(y, 567)

        # empty the list so we can use it again
        l.pop()
        l.pop()

    def test_hlist_get_index_error(self):
        l = HList(prefix='yo')
        self.assertEqual(l.get(10000), None)

    def test_hlist_set(self):
        l = HList(prefix='yo')
        l.push(123)
        l.push(567)

        l.set(1, 890)
        l.set(0, 166)

        x = l.get(1)
        y = l.get(0)

        self.assertEqual(x, 890)
        self.assertEqual(y, 166)

        # empty the list so we can use it again
        l.pop()
        l.pop()

    def test_hlist_set_index_error(self):
        l = HList(prefix='yo')

        with self.assertRaises(redis.exceptions.ResponseError):
            l.set(10000, 123)

    def test_hlist_pop_right(self):
        l = HList(prefix='yo')

        l.push(123)
        l.push(456)

        x = l.pop_right()

        self.assertEqual(x, 123)

        l.pop()

    def test_hlist_append(self):
        l = HList(prefix='yo')

        l.push(123)
        l.append(456)

        x = l.pop_right()

        self.assertEqual(x, 456)

        l.pop()

    def test_hlist_extend(self):
        l = HList(prefix='yo')

        l.extend([1, 2, 3, 4, 5])

        a = l.pop()
        b = l.pop()
        c = l.pop()
        d = l.pop()
        e = l.pop()

        self.assertEqual(a, 1)
        self.assertEqual(b, 2)
        self.assertEqual(c, 3)
        self.assertEqual(d, 4)
        self.assertEqual(e, 5)