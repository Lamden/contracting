from seneca.libs.metering.estimator import OperationsEstimator
from tests.utils import recur_fibo
import dis, sys, os, time

class Cost:

    def __init__(self):
        self.estimator = OperationsEstimator()
        self.cost = 0

    def nop(self, code_obj):
        exec(code_obj)

    def pre(self):
        self.oldtrace = sys.gettrace()
        sys.settrace(self.trace)

    def post(self):
        sys.settrace(self.oldtrace)

    def compile(self, code_str):
        return compile(code_str, '__main__', 'exec')

    def compute_cost(self, code_obj):
        self.cost = 0
        exec(code_obj)
        return self.cost

    def trace(self, frame, event, arg):
        try:
            assert event == 'line'
            self.cost += self.estimator.cu_costs[frame.f_code.co_code[frame.f_lasti]]
        except:
            pass
        return self.trace
