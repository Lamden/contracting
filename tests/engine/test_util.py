from unittest import TestCase
from seneca.engine.util import *
import unittest

class TestUtil(TestCase):
    def test_fst(self):
        self.assertEqual(fst((1, 2)), 1)

    def test_snd(self):
        self.assertEqual(snd((1, 2)), 2)

    def test_swap(self):
        self.assertEqual(swap((1, 2)), (2, 1))

    def test_f_apply(self):
        self.assertEqual(f_apply(lambda x: x, 1), 1)

    def test_intercalate(self):
        self.assertEqual(intercalate('_', 'abcde'), 'a_b_c_d_e')
        self.assertEqual(intercalate('_', [None, 'a', None, 'b']), 'a_b')

    def test_add_methods(self):
        def id_(self, x):
            return x

        @add_methods(id_)
        class Test(object):
            pass

        t = Test()
        self.assertEqual(t.id_('abc'), 'abc')

    def test_add_methods_as(self):
        def id_(self, x):
            return x

        @add_method_as(id_, 'id_')
        class Test(object):
            pass

        t = Test()
        self.assertEqual(t.id_('abc'), 'abc')

    def test_filter_split(self):
        self.assertEqual(filter_split(lambda x: x == 'x', 'aaxbbxccxddx'),
                         (['x', 'x', 'x', 'x'], ['a', 'a', 'b', 'b', 'c', 'c', 'd', 'd']))

    def test_dict_to_nt(self):
        d = dict_to_nt({'x': 'y'})
        self.assertEqual(str(d), "seneca_generate_type(x='y')")

    def test_dict_to_obj(self):
        self.assertEqual(str(dict_to_obj({'x': 'y'}).x), 'y')

    def test_manual_import(self):
        m = manual_import(__file__, 'tester')
        self.assertEqual(type(m), dict)
        self.assertTrue('manual_import' in m.keys())



if __name__ == '__main__':
    unittest.main()
