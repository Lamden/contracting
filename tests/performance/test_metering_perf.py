import timeit, time

setup = '''
from seneca.libs.metering.cost import Cost
from tests.utils import recur_fibo
code_str = "recur_fibo(20)"
code_obj = compile(code_str, '__main__', 'exec')
c = Cost()
'''
raw = timeit.timeit('''
print('raw')
c.nop(code_obj)
''', setup=setup, number=10, timer=time.clock)
tracing = timeit.timeit('''
print('trace')
c.compute_cost(code_obj)
''', setup=setup+'\nc.pre()', number=10, timer=time.clock)
print(raw)
print(tracing)
print(tracing/raw, 'ratio')
