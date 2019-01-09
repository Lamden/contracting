from seneca.tooling import *
from seneca.engine.interpreter import Seneca
Seneca.interface.r.flushdb()

def tau():
    from seneca.libs.datatypes import hmap

    balances = hmap('balances', str, int)

    @export
    def transfer(to, amount):
        assert balances[rt['sender']] >= amount

        balances[to] += amount
        balances[rt['sender']] -= amount

    # a better way to deal with 'allowances' which are dumb af
    # and don't reflect real life business operations
    custodials = hmap('custodials', str, hmap(None, str, int))

    @export
    def add_to_custodial(to, amount):
        assert balances[rt['sender']] >= amount

        custodials[rt['sender']][to] += amount
        balances[rt['sender']] -= amount

    @export
    def remove_from_custodial(to, amount):
        assert custodials[rt['sender']][to] >= amount

        balances[rt['sender']] += amount
        custodials[rt['sender']][to] -= amount

    @export
    def spend_custodial(_from, amount, to):
        assert custodials[_from][rt['sender']] >= amount

        balances[to] += amount
        custodials[_from][rt['sender']] -= amount

    @seed
    def seed():
        balances['stu'] = 1000000

contract = publish_function(tau, 'tau', 'stu')
