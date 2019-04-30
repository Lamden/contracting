"""
    OperationsEstimator is for computing the estimated cost of each opcode
    instructions for your system. This is not meant to be used for determining
    the cost of a smart contract. For that, see contracting.libs.metering.cost.Cost
"""

import dis, time, os, sys, numpy as np
from collections import defaultdict
from scipy.optimize import nnls
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

import contracting

constants_path = contracting.__path__[0] + '/constants/'

def timeit(fn):
    def _fn(self, op, code_str, *args, **kwargs):

        ### Finding the median time it takes for each code snippets
        med = []
        opcode = dis.opmap[op]
        instructions = defaultdict(int)
        for ins in dis.get_instructions(code_str):
            instructions[ins.opcode] += 1
        code_obj = compile(code_str, '__main__', 'exec')
        for i in range(self.iterations):
            try:
                start = time.clock()
                fn(self, code_obj, *args, **kwargs)
                end = time.clock()
            except ValueError:
                end = time.clock()
            elapsed = end-start
            med.append(elapsed)
            if hasattr(self, 'histogram_file'):
                self.histogram_file.write('{},{}\n'.format(opcode, elapsed))

        t = np.median(med)
        # if not instructions.get(opcode):
        #     raise Exception('Not a valid example: {}\n{}'.format(op,
        #         [ins.opname for ins in dis.get_instructions(code_str)]))
        self.costs[opcode] = {
            't': t,
            'ops': instructions
        }

        return t
    return _fn

def suppress_stdout(fn):
    def _fn(*args, **kwargs):
        ### Disable stdout
        stdout = sys.stdout
        f = open(os.devnull, 'w')
        sys.stdout = f
        fn(*args, **kwargs)
        ### Re-enable stdout
        sys.stdout = stdout
    return _fn

class OperationsEstimator:
    def __init__(self, show_plot=False):
        self.iterations = 10000
        self.total_opcodes = 144
        self.non_zero_min_cost = np.float('2.7937841015807387e-09')
        self.costs = {}
        self.histogram_fname = os.path.join(constants_path, 'histogram.csv')
        self.costs_fname = os.path.join(constants_path, 'costs.csv')
        self.cu_costs_fname = os.path.join(constants_path, 'cu_costs.const')
        self.show_plot = show_plot
        if not os.path.exists(self.costs_fname):
            self.compute_opcode_costs()
        else:
            self.load_opcode_costs()
        if not os.path.exists(self.cu_costs_fname):
            self.comput_cu_costs()
        else:
            self.load_cu_costs()

    @timeit
    def calc_cost(self, code_obj):
        exec(code_obj)

    @suppress_stdout
    def precalc_costs(self):
        self.calc_cost('POP_TOP','''
(lambda:1)()
        ''')
        self.calc_cost('ROT_TWO','''
a = 1; b = 2
(a, b) = (b, a)
        ''')
        self.calc_cost('ROT_THREE','''
a = 1
(a, a, a) = (a, a, a)
        ''')
        self.calc_cost('UNARY_POSITIVE','''
a = 1
a = +a
        ''')
        self.calc_cost('UNARY_NEGATIVE','''
a = 1
a = -a
        ''')
        self.calc_cost('UNARY_NOT','''
a = 1
a = not a
        ''')
        self.calc_cost('UNARY_INVERT','''
a = 1
a = ~a
        ''')
        self.calc_cost('BINARY_POWER','''
a = 2
a = a ** 2
        ''')
        self.calc_cost('BINARY_MULTIPLY','''
a = 2
a = a * 2
        ''')
        self.calc_cost('BINARY_MODULO','''
a = 2
a = a % 2
        ''')
        self.calc_cost('BINARY_ADD','''
a = 2
a = a + 2
        ''')
        self.calc_cost('BINARY_SUBTRACT','''
a = 2
a = a - 2
        ''')
        self.calc_cost('BINARY_SUBSCR','''
a = [1]
a[0]
        ''')
        self.calc_cost('BINARY_FLOOR_DIVIDE','''
a = 2
a = a // 2
        ''')
        self.calc_cost('BINARY_TRUE_DIVIDE','''
a = 2
a = a / 2
        ''')
        self.calc_cost('INPLACE_FLOOR_DIVIDE','''
a = 1
a //= 1
        ''')
        self.calc_cost('BUILD_SLICE','''
a = [1,2,3]
a = a[:]
        ''')
        self.calc_cost('INPLACE_ADD','''
a = 1
a += 1
        ''')
        self.calc_cost('INPLACE_SUBTRACT','''
a = 1
a -= 1
        ''')
        self.calc_cost('INPLACE_MULTIPLY','''
a = 1
a *= 1
        ''')
        self.calc_cost('INPLACE_TRUE_DIVIDE','''
a = 1
a /= 1
        ''')
        self.calc_cost('INPLACE_MODULO','''
a = 1
a %= 1
        ''')
        self.calc_cost('STORE_SUBSCR','''
a = [0]
a[0] = 1
        ''')
        self.calc_cost('DELETE_SUBSCR','''
a = [1]
del a[0]
        ''')
        self.calc_cost('BINARY_LSHIFT','''
a = 1
a = a << 1
        ''')
        self.calc_cost('BINARY_RSHIFT','''
a = 1
a = a >> 1
        ''')
        self.calc_cost('BINARY_AND','''
a = 1
a = a & 1
        ''')
        self.calc_cost('BINARY_XOR','''
a = 1
a = a ^ 1
        ''')
        self.calc_cost('BINARY_OR','''
a = 1
a = a | 1
        ''')
        self.calc_cost('INPLACE_POWER','''
a = 1
a **= 1
        ''')
        self.calc_cost('GET_ITER','''
for a in (1,2): pass
        ''')
        self.calc_cost('INPLACE_LSHIFT','''
a = 1
a <<= 1
        ''')
        self.calc_cost('INPLACE_RSHIFT','''
a = 1
a >>= 1
        ''')
        self.calc_cost('INPLACE_AND','''
a = 1
a &= 1
        ''')
        self.calc_cost('INPLACE_XOR','''
a = 1
a ^= 1
        ''')
        self.calc_cost('INPLACE_OR','''
a = 1
a |= 1
        ''')
        self.calc_cost('BREAK_LOOP','''
for a in (1,2): break
        ''')
        f = open('1.txt', 'w+')
        self.calc_cost('WITH_CLEANUP_START','''
with open("1.txt") as f:
    print(f.read())
        ''')
        self.calc_cost('WITH_CLEANUP_FINISH','''
with open("1.txt") as f:
    print(f.read())
        ''')
        os.remove('1.txt')
        self.calc_cost('RETURN_VALUE','''
# empty file
        ''')
        self.calc_cost('IMPORT_STAR','''
from sys import *
        ''')
        self.calc_cost('POP_BLOCK','''
for a in (1,2): break
        ''')
        self.calc_cost('END_FINALLY','''
try:
    a = 1
finally:
    a = 3
        ''')
        self.calc_cost('LOAD_BUILD_CLASS','''
class a: pass
        ''')
        self.calc_cost('STORE_NAME','''
a = 1
        ''')
        self.calc_cost('DELETE_NAME','''
a = 1
del a
        ''')
        self.calc_cost('UNPACK_SEQUENCE','''
(a, b) = "ab"
        ''')
        self.calc_cost('FOR_ITER','''
for i in (1,2): pass
        ''')
        self.calc_cost('STORE_ATTR','''
import sys
sys.stderr = sys.stdout
        ''')
        self.calc_cost('DELETE_ATTR','''
import random
random.hello = 'world'
del random.hello
        ''')
        self.calc_cost('STORE_GLOBAL','''
global a
a = 1
        ''')
        self.calc_cost('DELETE_GLOBAL','''
global a
a = 2
del a
        ''')
        self.calc_cost('DUP_TOP_TWO','''
a = 0
b = [0]
b[a] += 1
        ''')
        self.calc_cost('LOAD_CONST','''
a = 1
        ''')
        self.calc_cost('LOAD_NAME','''
a = 1
a = a
        ''')
        self.calc_cost('BUILD_TUPLE','''
a = 1;
a = (a, a)
        ''')
        self.calc_cost('BUILD_LIST','''
[1,2,3]
        ''')
        self.calc_cost('BUILD_CONST_KEY_MAP','''
{"a":1,"b":2}
        ''')
        self.calc_cost('LOAD_ATTR','''
[].sort()
        ''')
        self.calc_cost('COMPARE_OP','''
a = 1 == 2
        ''')
        self.calc_cost('IMPORT_NAME','''
import random
        ''')
        self.calc_cost('IMPORT_FROM','''
from dis import opmap
        ''')
        self.calc_cost('JUMP_FORWARD','''
if 1 == 2: pass
else: pass
        ''')
        self.calc_cost('POP_JUMP_IF_FALSE','''
if 1 == 2: pass
else: pass
        ''')
        self.calc_cost('POP_JUMP_IF_TRUE','''
if not(1 == 2): pass
else: pass
        ''')
        self.calc_cost('JUMP_ABSOLUTE','''
for i in (1,2): pass
        ''')
        self.calc_cost('LOAD_GLOBAL','''
global a
a = 1
a = a
        ''')
        self.calc_cost('CONTINUE_LOOP','''
for x in (1,2):
    try: continue
    except: pass
        ''')
        self.calc_cost('SETUP_LOOP','''
while 0 > 1: pass
        ''')
        self.calc_cost('SETUP_EXCEPT','''
try:
    a = 1
except ValueError:
    a = 2
        ''')
        self.calc_cost('SETUP_FINALLY','''
try:
    a = 1
finally:
    a = 3
        ''')
        self.calc_cost('RAISE_VARARGS','''
raise ValueError
        ''')
        self.calc_cost('CALL_FUNCTION','''
def f(): pass
f()
        ''')
        self.calc_cost('MAKE_FUNCTION','''
def f(): pass
        ''')
        self.calc_cost('BUILD_SLICE','''
a = [1,2,3,4]
b = a[::-1]
        ''')
        self.calc_cost('CALL_FUNCTION_EX','''
def f(a,b): pass
a = (1,2)
f(*a)
        ''')

    def computer_medians(self):
        X = []
        y = []
        for opcode, item in self.costs.items():
            X.append([item['ops'][i] if item['ops'].get(i) else 0 for i in range(self.total_opcodes)])
            y.append(item['t'])
        X = np.array(X)
        y = np.array(y)
        medians = np.array(nnls(X, y)[0])
        self.opcodes = [i for i in range(self.total_opcodes)]
        self.medians = [m for idx, m in enumerate(medians)]
        self.costs = {}
        for i, m in enumerate(self.medians):
            self.costs_file.write('{},{}\n'.format(self.opcodes[i], repr(m)))

    def plot(self):
        plt.plot(self.opcodes, self.medians, 'o', markersize=5)
        plt.legend()
        plt.show()

    def compute_opcode_costs(self):
        self.histogram_file = open(self.histogram_fname, 'w+')
        self.costs_file = open(self.costs_fname, 'w+')
        self.precalc_costs()
        self.computer_medians()
        if self.show_plot: self.plot()

    def load_opcode_costs(self):
        self.medians = []
        with open(self.costs_fname) as f:
            for line in f:
                opcode, median = line.split(',')
                self.medians.append(np.float(median))

    def comput_cu_costs(self):
        self.cu_costs_file = open(self.cu_costs_fname, 'w+')
        self.cu_costs = {}
        costs = np.array(self.medians)/self.non_zero_min_cost + 1.0 # 1.0 is padding for 0 costs
        for opcode, m in enumerate(costs):
            self.cu_costs[opcode] = int(np.round(m))
            self.cu_costs_file.write('{},{}\n'.format(opcode, self.cu_costs[opcode]))

    def load_cu_costs(self):
        self.cu_costs = {}
        with open(self.cu_costs_fname) as f:
            for line in f:
                opcode, cost = line.split(',')
                self.cu_costs[int(opcode)] = int(cost)
