from seneca.tooling import *
from seneca.engine.interpreter import Seneca
Seneca.interface.r.flushdb()

def stu_bucks():
    from seneca.libs.datatypes import hmap

    balances = hmap(prefix='balances',
                    key_type=str,
                    value_type=float)
    @seed
    def seed():
        balances['stu'] = 1234.0

    @export
    def check_balance(address):
        return balances[address]


def davis_dollars():
    from seneca.libs.datatypes import hmap

    balances = hmap(prefix='balances',
                    key_type=str,
                    value_type=float)
    @seed
    def seed():
        balances['davis'] = 4321.0 # Both tokens are the same except for this.

    @export
    def check_balance(address):
        return balances[address]

publish_function(stu_bucks, 'stu_bucks', 'stu')
publish_function(davis_dollars, 'davis_dollars', 'davis')

def dynamic_import():
    from seneca.libs.importing import import_contract

    @export
    def get_token_balance(token_name, account):
        token = import_contract(token_name)
        return token.check_balance(account)

contract = publish_function(dynamic_import, 'dynamic_import', 'stu')
stu = contract.get_token_balance(token_name='stu_bucks', account='stu')
davis = contract.get_token_balance(token_name='davis_dollars', account='davis')
print(stu)
print(davis)
