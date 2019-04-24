from unittest import TestCase
from seneca.stdlib.bridge.time import Datetime
from datetime import datetime as dt


class TestDatetime(TestCase):
    def test_datetime_variables_set(self):
        now = dt.now()
        now_str = dt.isoformat(now)

        d = Datetime(now_str)

        self.assertEqual(now.microsecond, d.microsecond)
        self.assertEqual(now.second, d.second)
        self.assertEqual(now.minute, d.minute)
        self.assertEqual(now.hour, d.hour)
        self.assertEqual(now.day, d.day)
        self.assertEqual(now.month, d.month)
        self.assertEqual(now.year, d.year)