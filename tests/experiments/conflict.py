from seneca.tooling import *
from seneca.engine.interpreter import Seneca
Seneca.interface.r.flushdb()

def c_1():
    from seneca.libs.datatypes import hmap
    resource = hmap('resource', str, int)

    @seed
    def seed():
        resource['stu'] = 1337
        resource['davis'] = 999

    @export
    def read_resource(string):
        return resource[string]

    @export
    def write_resource(string, value):
        resource[string] = value

def c_2():
    from seneca.contracts.c_1 import read_resource as r
    from seneca.contracts.c_1 import write_resource as w

    from seneca.libs.datatypes import hmap
    resource = hmap('resource', str, int)

    @seed
    def seed():
        resource['stu'] = 888
        resource['davis'] = 7777

    @export
    def read_resource(string):
        return resource[string]

    @export
    def read_other_resource(string):
        return r(address=string)

    @export
    def corrupt_resource(string, value):
        w(string=string, value=value)


# Publish both smart contracts
contract_1 = publish_function(c_1, 'c_1', 'stu')
contract_2 = publish_function(c_2, 'c_2', 'stu')

# Read the seperate resources on each
print(contract_1.read_resource(string='stu'))
print(contract_1.read_resource(string='davis'))

print(contract_2.read_resource(string='stu'))
print(contract_2.read_resource(string='davis'))

# Attempt to read the resource from the 1nd contract by calling the 2nd.
# This will return resources from the 2nd.
print(contract_2.read_other_resource(string='stu'))
print(contract_2.read_other_resource(string='davis'))

# Attempt to write / call a write method on the 1st contract by calling the 2nd.
print(contract_2.corrupt_resource(string='stu', value=100))
print(contract_2.corrupt_resource(string='davis', value=123))

# This will actually corrupt the data on the 2nd.
print(contract_1.read_resource(string='stu'))
print(contract_1.read_resource(string='davis'))

# 1st contract is not affected
print(contract_2.read_resource(string='stu'))
print(contract_2.read_resource(string='davis'))
