from seneca.libs.metering.cost import Cost

c = Cost()
c.pre()
print(c.compute_cost(c.compile('''
a = 1
a = 2
a = 4
a = 1
''')), 'CUs')
print(c.compute_cost(c.compile('''
balances = {'hello': 'world'}
balances['hello'] = 'goodbye'
''')), 'CUs')
print(c.compute_cost(c.compile('''
balances = {'hello': 'world'}
for i in range(100):
    balances['hello'] = 'goodbye'
''')), 'CUs')
print(c.compute_cost(c.compile('''
balances = {'hello': 'world'}
for i in range(1000):
    balances['hello'] = 'goodbye'
''')), 'CUs')
print(c.compute_cost(c.compile('''
a=(0,1,2,3, ... ,65535)
''')), 'CUs')
c.post()
