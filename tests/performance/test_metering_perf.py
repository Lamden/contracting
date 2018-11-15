import timeit, time

setup = '''
from tests.utils import recur_fibo
code_str = "recur_fibo(20)"
code_obj = compile(code_str, '__main__', 'exec')
class Cost:
    @classmethod
    def nop(cls, code_obj, recur_fibo):
        exec(code_obj)
c = Cost()
'''
raw = timeit.timeit('''
c.nop(code_obj, recur_fibo)
print('Raw execution.')
''', setup=setup, number=10, timer=time.clock)

tracing_setup = '''
from tracer import Tracer
import seneca, os
from os.path import join

seneca_path = seneca.__path__[0]
path = join(seneca_path, 'constants', 'cu_costs.const')
os.environ['CU_COST_FNAME'] = path

from tests.utils import recur_fibo
code_str = "__tracer__.set_stamp(50000); __tracer__.start(); recur_fibo(20); __tracer__.stop()"
code_obj = compile(code_str, '__main__', 'exec')
t = Tracer()
'''
tracing = timeit.timeit('''
exec(code_obj, {'__tracer__': t, 'recur_fibo': recur_fibo})
# cost = t.get_stamp_used()
# print('Metered execution ({} CUs)'.format(cost))
''', setup=tracing_setup, number=10, timer=time.clock)

print(raw)
print(tracing)
print(tracing/raw, 'ratio')
