import timeit, time

setup = '''
from seneca.libs.metering.cost import Cost
from tests.utils import recur_fibo
code_str = "recur_fibo(20)"
code_obj = compile(code_str, '__main__', 'exec')
c = Cost()
'''
raw = timeit.timeit('''
c.nop(code_obj)
print('Raw execution.')
''', setup=setup, number=10, timer=time.clock)

tracing_setup = '''
from seneca.libs.metering.tracer import Tracer
import seneca, os
from os.path import join

seneca_path = seneca.__path__[0]
path = join(seneca_path, 'constants', 'cu_costs.const')
os.environ['CU_COST_FNAME'] = path

from tests.utils import recur_fibo
code_str = "recur_fibo(20)"
code_obj = compile(code_str, '__main__', 'exec')
t = Tracer()

'''
tracing = timeit.timeit('''
t.set_gas(50000)
t.start()
exec(code_obj)
cost = t.get_gas_used()
t.stop()
print('Metered execution ({} CUs)'.format(cost))
''', setup=tracing_setup, number=10, timer=time.clock)

print(raw)
print(tracing)
print(tracing/raw, 'ratio')
