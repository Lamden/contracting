from unittest import TestCase
from seneca.libs.runtime import *

class TestContactData(TestCase):
    x = make_n_tup(make_exports([('test_author', 'test_contract_addr')]))
    print(x.sender)
