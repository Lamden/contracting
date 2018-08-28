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

        self.l = HList(prefix='yo')

        # clears the list so it's easier to push and pop to / test
        while self.l.pop() is not None:
            pass

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

        print(good_map)

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
        self.assertEqual(self.l.rep(), ':list:yo:int:')
        self.assertEqual(self.l.p, 'yo:')

    def test_hlist_push_pop(self):
        self.l.push(123)

        with self.assertRaises(AssertionError):
            self.l.push('123')

        x = self.l.pop()

        self.assertEqual(x, 123)

    def test_hlist_get(self):
        self.l.push(123)
        self.l.push(567)

        x = self.l.get(1)
        y = self.l.get(0)

        self.assertEqual(x, 123)
        self.assertEqual(y, 567)

        # empty the list so we can use it again
        self.l.pop()
        self.l.pop()

    def test_hlist_get_index_error(self):
        self.assertEqual(self.l.get(10000), None)

    def test_hlist_set(self):
        self.l.push(123)
        self.l.push(567)

        self.l.set(1, 890)
        self.l.set(0, 166)

        x = self.l.get(1)
        y = self.l.get(0)

        self.assertEqual(x, 890)
        self.assertEqual(y, 166)

        # empty the list so we can use it again
        self.l.pop()
        self.l.pop()

    def test_hlist_set_index_error(self):

        with self.assertRaises(redis.exceptions.ResponseError):
            self.l.set(10000, 123)

    def test_hlist_pop_right(self):

        self.l.push(123)
        self.l.push(456)

        x = self.l.pop_right()

        self.assertEqual(x, 123)

        self.l.pop()

    def test_hlist_append(self):

        self.l.push(123)
        self.l.append(456)

        x = self.l.pop_right()

        self.assertEqual(x, 456)

        self.l.pop()

    def test_hlist_extend(self):

        self.l.extend([1, 2, 3, 4, 5])

        a = self.l.pop()
        b = self.l.pop()
        c = self.l.pop()
        d = self.l.pop()
        e = self.l.pop()

        self.assertEqual(a, 1)
        self.assertEqual(b, 2)
        self.assertEqual(c, 3)
        self.assertEqual(d, 4)
        self.assertEqual(e, 5)

    def test_hlist_getitem_setitem(self):

        self.l.push(123)
        self.l[0] = 123456789

        self.assertEqual(self.l[0], 123456789)

        self.l.pop()

    def test_hlist_convenience_methods(self):
        p = hlist()

        self.assertTrue(isinstance(p, Placeholder))
        self.assertTrue(p.value_type == int)

        ll = hlist('hello_there')
        self.assertTrue(isinstance(ll, HList))
        self.assertEqual(ll.prefix, 'hello_there')
        self.assertEqual(p.value_type, int)

    def test_hlist_store_placeholders(self):
        pass

    def test_table_init(self):
        t = Table(prefix='holla', schema={'name': str, 'balance': int})

        self.assertEqual(t.schema, {'name': str, 'balance': int})
        self.assertEqual(t.p, 'holla:')

        with self.assertRaises(AssertionError):
            bad_t = Table(prefix='bad_boy', schema={'howdy': 'partner'})

        with self.assertRaises(AssertionError):
            bad_t = Table(prefix='oh_no', schema={1: True})

    def test_table_schema_matching(self):
        t = Table(prefix='holla', schema={'name': str, 'balance': int})

        good_dict = {'name': 'stu', 'balance': 100}
        subset_dict = {'name': 'stu'}

        mismatched_type_dict = {'name': 1, 'balance': '100'}
        wrong_keys_dict = {'pizza_hut': 'taco_bell', 'im_at_the': 123}


        t.dict_matches_schema(good_dict)
        t.dict_matches_schema(subset_dict)

        with self.assertRaises(AssertionError):
            t.dict_matches_schema(mismatched_type_dict)

        with self.assertRaises(AssertionError):
            t.dict_matches_schema(wrong_keys_dict)

    def test_table_encoding_variable(self):
        t = Table(prefix='holla', schema={'name': str, 'balance': int})

        v = t.encode_value(1, int)
        self.assertEqual(v, b'1')

        with self.assertRaises(AssertionError):
            t.encode_value('b', int)

    def test_table_encoding_placeholders(self):
        p = ListPlaceholder()

        t = Table(prefix='complex', schema={'name': str, 'list': p})

        repr_str = ':list:some_list:int:'
        l = parse_representation(repr_str)

        v = t.encode_value(l, p)

        self.assertEqual(v, repr_str.encode())
