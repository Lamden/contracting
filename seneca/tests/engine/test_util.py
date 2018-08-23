from unittest import TestCase
from seneca.engine.util import fst


class TestUtil(TestCase):
    def test_fst(self):
        self.assertEqual(fst((1,2)), 1)

    def test_snd(self):
        self.assertEqual(snd((1,2)), 2)