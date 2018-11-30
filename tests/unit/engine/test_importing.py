from unittest import TestCase
from seneca.engine.interface import SenecaInterface
from seneca.libs.importing import import_contract


class TestImporting(TestCase):

    def test_setup(self):
        with SenecaInterface(concurrent_mode=False, port=6379, password='') as interface:
            t = import_contract('token')
            t.balance_of('stu')