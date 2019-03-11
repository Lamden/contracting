from seneca.libs.metering.tracer import Tracer
import seneca, os
from os.path import join

seneca_path = seneca.__path__[0]
path = join(seneca_path, 'constants', 'cu_costs.const')
os.environ['CU_COST_FNAME'] = path

def measure_this():
    return 'yes'

t = Tracer()
t.set_stamp(1000)
t.start()

a = 1
b = 2
a = b
measure_this()

t.stop()
cost = t.get_stamp_used()
print('cost=',cost)
