from seneca.libs.metering.estimator import OperationsEstimator
import dis, sys, os

# if __name__ == '__main__':
#     import os
#     os.system('rm *.csv')

class Cost:

    def __init__(self):
        self.estimator = OperationsEstimator()

    def get_cost(self):
        return int(os.getenv('__COST__', '0'))

    def set_cost(self, cost):
        os.environ['__COST__'] = str(cost)

    # FOR EXECUTION WITH TRACE
    def compute_cost(self, code_str):
        code_obj = compile(code_str, '__main__', 'exec')
        self.set_cost(0)
        oldtrace = sys.gettrace()
        sys.settrace(self.trace)
        exec(code_obj)
        sys.settrace(oldtrace)
        return self.get_cost()

    def trace(self, frame, event, arg):
        cost = self.get_cost()
        if event == 'line':
            for ins in dis.get_instructions(frame.f_code):
                cost += self.estimator.cu_costs[ins.opcode]
                self.set_cost(cost)
        return self.trace

if __name__ == '__main__':
    c = Cost()
    print(c.compute_cost('''
a = 1
a = 2
a = 4
a = 1
    '''), 'CUs')
    print(c.compute_cost('''
balances = {'hello': 'world'}
balances['hello'] = 'goodbye'
    '''), 'CUs')
    print(c.compute_cost('''
balances = {'hello': 'world'}
for i in range(100):
    balances['hello'] = 'goodbye'
    '''), 'CUs')
    print(c.compute_cost('''
balances = {'hello': 'world'}
for i in range(1000):
    balances['hello'] = 'goodbye'
    '''), 'CUs')
    print(c.compute_cost('''
a=(0,1,2,3, ... ,65535)
    '''), 'CUs')
