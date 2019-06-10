from unittest import TestCase
from contracting.stdlib.bridge import imports


class TestImports(TestCase):
    def test_func_correct_type(self):
        def sup(x, y):
            return x + y

        s = imports.Func(name='sup', args=('x', 'y'))

        self.assertTrue(s.is_of(sup))

    def test_func_incorrect_name(self):
        def sup(x, y):
            return x + y

        s = imports.Func(name='not_much', args=('x', 'y'))

        self.assertFalse(s.is_of(sup))

    def test_func_incorrect_args(self):
        def sup(a, b):
            return a + b

        s = imports.Func(name='sup', args=('x', 'y'))

        self.assertFalse(s.is_of(sup))

    def test_func_correct_with_kwargs(self):
        def sup(x=100, y=200):
            return x + y

        s = imports.Func(name='sup', args=('x', 'y'))

        self.assertTrue(s.is_of(sup))

    def test_func_correct_with_annotations(self):
        def sup(x: int, y: int):
            return x + y

        s = imports.Func(name='sup', args=('x', 'y'))

        self.assertTrue(s.is_of(sup))

    def test_func_correct_with_kwargs_and_annotations(self):
        def sup(x: int=100, y: int=100):
            return x + y

        s = imports.Func(name='sup', args=('x', 'y'))

        self.assertTrue(s.is_of(sup))

    def test_func_correct_private(self):
        def __sup(a, b):
            return a + b

        s = imports.Func(name='sup', args=('a', 'b'), private=True)

        self.assertTrue(s.is_of(__sup))

    def test_func_false_private(self):
        def __sup(a, b):
            return a + b

        s = imports.Func(name='sup', args=('x', 'y'), private=True)

        self.assertFalse(s.is_of(__sup))