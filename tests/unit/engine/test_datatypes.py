import unittest

from unittest import TestCase
from seneca.engine.interface import SenecaInterface
from seneca.engine.interpreter import SenecaInterpreter, Seneca
from seneca.libs.datatypes import *
from seneca.libs.decimal import make_decimal
from seneca.constants.config import get_redis_port, MASTER_DB, DB_OFFSET, get_redis_password

'''
test complex key types and value types
test more failure cases
'''


class TestDatatypes(TestCase):

    def setUp(self):
        self.interface = SenecaInterface(False)
        Seneca.concurrent_mode = False
        Seneca.loaded = {'__main__': {'rt': {'author': 'me', 'sender': 'me', 'contract': 'currency'}}}
        self.r = self.interface.r
        self.l = HList(prefix='yo')
        self.r.flushdb()

    def test_type_mappings(self):
        self.assertTrue(type_to_string[str] == 'str')
        self.assertTrue(type_to_string[int] == 'int')
        self.assertTrue(type_to_string[bool] == 'bool')

        self.assertTrue(string_to_type['str'] == str)
        self.assertTrue(string_to_type['int'] == int)
        self.assertTrue(string_to_type['bool'] == bool)

    def test_parse_representation_map(self):
        repr_str = '*hmap<currency:test>(int,str)'
        m = parse_representation(repr_str)

        self.assertTrue(type(m) == HMap)
        self.assertTrue(m.key_type == int)
        self.assertTrue(m.value_type == str)

    def test_placeholder(self):
        p = Placeholder(placeholder_type=HMap)

        self.assertTrue(p.key_type == str)
        self.assertTrue(p.value_type == int)
        self.assertTrue(p.placeholder_type == HMap)

        good_repr_str = '*hmap<currency:some_map>(str,int)'
        good_map = parse_representation(good_repr_str)

        self.assertTrue(p.valid(good_map))

        bad_repr_str = '*hmap<currency:some_other_map>(int,str)'
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

        repr_str = '*hmap<currency:howdy>(str,int)'
        _map = parse_representation(repr_str)

        v = r.encode_value(_map)

        self.assertTrue(type(v), bytes)
        self.assertTrue(v.decode(), repr_str)

    def test_robject_decoding_variable(self):
        r = RObject()
        self.assertTrue(r.decode_value(b'1'), 1)
        self.assertTrue(r.decode_value(b'"s"'), 's')
        self.assertTrue(r.decode_value(b'[1, 2, 3]'), [1, 2, 3])

        repr_str = b'*hmap<currency:howdy>(str,int)'
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
        self.assertEqual(n, 0)

    def test_hmap_convenience_function(self):
        m = hmap()
        self.assertTrue(isinstance(m, Placeholder))

        m2 = hmap('howdy')
        self.assertTrue(isinstance(m2, HMap))

    def test_hlist_init_repr(self):
        self.assertEqual(self.l.rep(), '*hlist<currency:yo>(int)')
        self.assertEqual(self.l.prefix, 'currency:yo')

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
        self.assertEqual(ll.prefix, 'currency:hello_there')
        self.assertEqual(p.value_type, int)

    def test_hlist_store_placeholders(self):
        complex_l = hlist('goodtimes', value_type=hmap())

        complex_l.push(hmap('some map'))

        m = complex_l.pop()

        self.assertTrue(m.prefix, 'some map')

    def test_table_init(self):

        t = Table(prefix='holla', schema={'name': str, 'balance': int})

        self.assertEqual(t.schema, {'name': str, 'balance': int})
        self.assertEqual(t.p, 'currency:holla:')

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

        repr_str = '*hlist<currency:some_list>(int)'
        l = parse_representation(repr_str)

        v = t.encode_value(l, p)

        self.assertEqual(v, repr_str.encode())

    def test_table_set_get(self):
        pets = Table(prefix='pets', schema={'breed': str, 'owner': str, 'age': int})
        pets.set('henry', {'breed': 'mutt', 'owner': 'stu', 'age': 13})

        henry_all = pets.get('henry')
        henry_single = pets.get('henry', ('age',))
        henry_subset = pets.get('henry', ('owner', 'breed',))

        self.assertDictEqual(henry_all, {'breed': 'mutt', 'owner': 'stu', 'age': 13})
        self.assertDictEqual(henry_single, {'age': 13})
        self.assertDictEqual(henry_subset, {'breed': 'mutt', 'owner': 'stu'})

    def test_table_itemset_itemget(self):
        pets = Table(prefix='pets', schema={'breed': str, 'owner': str, 'age': int})
        pets['black_kitty'] = {'breed': 'fatso', 'owner': 'stu', 'age': 6}

        black_kitty = pets['black_kitty']

        self.assertDictEqual(black_kitty, {'breed': 'fatso', 'owner': 'stu', 'age': 6})

    def test_table_convenience_methods(self):
        p = table(schema={'breed': str, 'age': int})

        self.assertTrue(isinstance(p, TablePlaceholder))
        self.assertDictEqual(p.schema, {'breed': str, 'age': int})

        t = table(prefix='birbs', schema={'breed': str, 'age': int})
        self.assertTrue(isinstance(t, Table))

    def test_table_placeholder_validity(self):
        p = table(schema={'breed': str, 'age': int})
        t = table(prefix='birbs', schema={'breed': str, 'age': int})

        self.assertTrue(p.valid(t))

        bad_t = table(prefix='bribs', schema={'kaw': int, 'age': str})

        self.assertFalse(p.valid(bad_t))

    def test_table_list_placeholder_not_valid(self):
        lp = hlist()

        bad_l = hlist('BAD', value_type=str)

        self.assertFalse(lp.valid(bad_l))

    def test_table_repr_reconstruction(self):
        t = table(prefix='something', schema={'blah': int, 'blerg': str})

    def test_complex_type_repr(self):
        s = '*table({howdy:int,boiii:*hmap(str,int)})'
        t = parse_complex_type_repr(s)

        self.assertTrue(t.key_type == str)
        ph = t.schema['boiii']
        ph2 = hmap(key_type=str, value_type=int)

        self.assertEqual(ph.key_type, ph2.key_type)
        self.assertEqual(ph.value_type, ph2.value_type)

    def test_table_type_repr_with_prefix(self):
        s = '*table<currency:lazytown>({howdy:int,boiii:*hmap(str,int)})'
        t = parse_complex_type_repr(s)
        self.assertTrue(t.prefix, 'lazytown')

    def test_none_typing(self):
        s = hmap(prefix='hello', value_type=None)
        s.set('yo', 123)
        self.assertEqual(s.get('yo'), 123)

    def test_key_typing(self):
        s = hmap(prefix='hello', key_type=int)
        s.set(1, 123)
        _s = s.get(1)
        self.assertEqual(_s, 123)

    def test_complex_key_typing(self):
        s = hmap(prefix='hello', key_type=hmap())
        s.set(hmap(prefix='uhoh'), 123)

        self.assertEqual(s.get(hmap(prefix='uhoh')), 123)

    def test_none_typing_list(self):
        s = hlist(prefix='hello', value_type=None)
        s.push(123)
        self.assertEqual(s.pop(), 123)

    def test_key_typing_table(self):
        s = table(prefix='hello123', key_type=int, schema={'test1': int, 'test2': str})
        s.set(1, {'test1': 123, 'test2': 'hello'})
        _s = s.get(1)
        self.assertDictEqual(_s, {'test1': 123, 'test2': 'hello'})

    def test_complex_key_typing_table(self):
        s = table(prefix='hello123', key_type=hlist(), schema={'test1': int, 'test2': str})

        s.set(hlist(prefix='uhoh'), {'test1': 123, 'test2': 'hello'})

        _s = s.get(hlist(prefix='uhoh'))

        self.assertDictEqual(_s, {'test1': 123, 'test2': 'hello'})

    def test_table_representation(self):
        s = '*table<currency:lazytown>({howdy:int,boiii:*hmap(str,int)})'
        _s = table(prefix='lazytown', schema={'howdy': int, 'boiii': hmap()})
        self.assertEqual(s, _s.rep())

    def test_table_placeholder_rep(self):
        s = '*table({howdy:int,boiii:*hmap(str,int)})'
        _s = table(schema={'howdy': int, 'boiii': hmap()})
        self.assertEqual(s, _s.rep())

    def test_robject_raises_error(self):
        r = RObject()
        with self.assertRaises(NotImplementedError):
            r.rep()

    def test_robject_raises_on_none_type(self):
        with self.assertRaises(AssertionError):
            r = RObject(key_type=None)

    def test_complex_types(self):
        self.assertTrue(is_complex_type(hmap()))
        self.assertTrue(is_complex_type(hmap(prefix='ass')))
        self.assertFalse(is_complex_type('literally anything else'))

    def test_vivify_simple_types(self):
        h = hmap(prefix='yoyo')
        self.assertEqual(h['doesntexist'], 0)

        h = hmap(prefix='yoyo', value_type=str)
        self.assertEqual(h['doesntexist'], '')

        h = hmap(prefix='yoyo', value_type=bool)
        self.assertEqual(h['doesntexist'], False)

    def test_vivify_complex_types(self):
        h = hmap(prefix='yoyo', value_type=hmap())
        _h = h['sdgdfgdfg']
        self.assertEqual(_h.value_type, int)
        self.assertEqual(_h.key_type, str)
        self.assertEqual(_h.prefix, 'currency:yoyo.sdgdfgdfg')

        z = h['sdgdfgdfg']['blah']
        self.assertEqual(z, 0)

    def test_vivify_complex_list(self):
        h = hlist(prefix='yoyo', value_type=hlist())
        _h = h[0]
        self.assertEqual(_h.value_type, int)
        self.assertEqual(_h.prefix, 'currency:yoyo.0')

        z = h[0][0]
        self.assertEqual(z, 0)

    def test_ranked_add_get(self):
        r = Ranked(prefix='hello_there')
        r.add('stu', 1000)
        r.add('davis', 100)

        self.assertEqual(r.get_max(), 'stu')
        self.assertEqual(r.get_min(), 'davis')

    def test_ranked_delete(self):
        r = Ranked(prefix='hello_there2')
        r.add('stu', 1000)
        r.add('davis', 100)

        r.delete('stu')

        self.assertEqual(r.get_max(), 'davis')

    def test_ranked_increment(self):
        r = Ranked(prefix='delegates')

        r.increment('stu', 165)

        self.assertEqual(r.score('stu'), 165.0)

        r.delete('stu')

    def test_ranked_rep(self):
        r = Ranked('testing')
        r_str = r.rep()

        _r = parse_representation(r_str)

        self.assertEqual(_r.prefix, r.prefix)
        self.assertEqual(_r.key_type, r.key_type)
        self.assertEqual(_r.value_type, r.value_type)

    def test_drop(self):
        l = HList('something', str)
        l.push('yoyoyo')
        l.push('supsupsup')

        l.drop()

        self.assertEqual(l.pop(), None)

    def test_ranked_pop_max(self):
        r = ranked('woot', str, int)
        r.add('stu', 1000)
        r.add('davis', 1001)
        r.add('falcon', 999)

        _r = r.pop_max()
        self.assertEqual(_r, 'davis')

    def test_ranked_pop_min(self):
        r = ranked('woot', str, int)
        r.add('stu', 1000)
        r.add('davis', 1001)
        r.add('falcon', 999)

        _r = r.pop_min()
        self.assertEqual(_r, 'falcon')

    def test_exists_hlist(self):
        l = HList('bleh', str)
        l.push('stu')
        print(l.exists('stu'))

    def test_float_hmap(self):
        h = hmap('test', str, float)
        h.set('stu', 0.01)

        f = h.get('stu')

        self.assertTrue(isinstance(f, Decimal))
        self.assertEqual(Decimal('0.01'), f)

    def test_float_as_key_type(self):
        h = hmap('test3', float, float)
        h.set(0.1234, 22/7)

        f = h.get(0.1234)

        _f = make_decimal(22/7)

        self.assertTrue(isinstance(f, Decimal))
        self.assertEqual(_f, f)

    def test_simple_type_reprs(self):
        f = parse_representation('float')
        self.assertEqual(f, Decimal)

        f = parse_representation('bytes')
        self.assertEqual(f, bytes)

        f = parse_representation('bool')
        self.assertEqual(f, bool)

    def test_build_placeholder_list_from_repr(self):
        r = '*hlist(int)'
        l = build_list_from_repr(r)
        self.assertTrue(isinstance(l, ListPlaceholder))
        self.assertEqual(l.value_type, int)
        self.assertEqual(l.rep(), r)

    def test_build_placeholder_ranked_from_repr(self):
        r = '*ranked(int,str)'
        _r = build_ranked_from_repr(r)
        print(_r)
        self.assertTrue(isinstance(_r, RankedPlaceholder))
        self.assertEqual(_r.value_type, str)

if __name__ == '__main__':
    unittest.main()
