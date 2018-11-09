import dis, time, os, sys, numpy as np
from collections import defaultdict
from scipy.optimize import nnls
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

_ITERATION = 10000
costs = {}
relevant_ops = set()

def timeit(fn):
    def _fn(op, code_str, *args, **kwargs):

        ### Average the cost
        med = []
        opcode = dis.opmap[op]
        relevant_ops.add(opcode)
        instructions = defaultdict(int)
        for ins in dis.get_instructions(code_str):
            instructions[ins.opcode] += 1
        code_obj = compile(code_str, '__main__', 'exec')
        for i in range(_ITERATION):
            try:
                start = time.clock()
                fn(code_obj, *args, **kwargs)
                end = time.clock()
            except ValueError:
                end = time.clock()
            elapsed = end-start
            med.append(elapsed)
            histogram_file.write('{},{}\n'.format(opcode, elapsed))

        t = np.median(med)
        if not instructions.get(opcode):
            raise Exception('Not a valid example: {}\n{}'.format(op,
                [ins.opname for ins in dis.get_instructions(code_str)]))
        costs[opcode] = {
            't': t,
            'ops': instructions
        }

        return t
    return _fn

@timeit
def calc_cost(code_obj):
    return exec(code_obj)

def suppress_stdout(fn):
    def _fn(*args, **kwargs):
        ### Disable stdout
        stdout = sys.stdout
        f = open(os.devnull, 'w')
        sys.stdout = f
        fn(*args, **kwargs)
        ### Reenable stdout
        sys.stdout = stdout
    return _fn

# @suppress_stdout
def precalc_costs():
    calc_cost('POP_TOP','''
(lambda:1)()
    ''')
    calc_cost('ROT_TWO','''
a = 1; b = 2
(a, b) = (b, a)
    ''')
    calc_cost('ROT_THREE','''
a = 1
(a, a, a) = (a, a, a)
    ''')
    calc_cost('UNARY_POSITIVE','''
a = 1
a = +a
    ''')
    calc_cost('UNARY_NEGATIVE','''
a = 1
a = -a
    ''')
    calc_cost('UNARY_NOT','''
a = 1
a = not a
    ''')
    calc_cost('UNARY_INVERT','''
a = 1
a = ~a
    ''')
    calc_cost('BINARY_POWER','''
a = 2
a = a ** 2
    ''')
    calc_cost('BINARY_MULTIPLY','''
a = 2
a = a * 2
    ''')
    calc_cost('BINARY_MODULO','''
a = 2
a = a % 2
    ''')
    calc_cost('BINARY_ADD','''
a = 2
a = a + 2
    ''')
    calc_cost('BINARY_SUBTRACT','''
a = 2
a = a - 2
    ''')
    calc_cost('BINARY_SUBSCR','''
a = [1]
a[0]
    ''')
    calc_cost('BINARY_FLOOR_DIVIDE','''
a = 2
a = a // 2
    ''')
    calc_cost('BINARY_TRUE_DIVIDE','''
a = 2
a = a / 2
    ''')
    calc_cost('INPLACE_FLOOR_DIVIDE','''
a = 1
a //= 1
    ''')
    calc_cost('BUILD_SLICE','''
a = [1,2,3]
a = a[:]
    ''')
    calc_cost('INPLACE_ADD','''
a = 1
a += 1
    ''')
    calc_cost('INPLACE_SUBTRACT','''
a = 1
a -= 1
    ''')
    calc_cost('INPLACE_MULTIPLY','''
a = 1
a *= 1
    ''')
    calc_cost('INPLACE_TRUE_DIVIDE','''
a = 1
a /= 1
    ''')
    calc_cost('INPLACE_MODULO','''
a = 1
a %= 1
    ''')
    calc_cost('STORE_SUBSCR','''
a = [0]
a[0] = 1
    ''')
    calc_cost('DELETE_SUBSCR','''
a = [1]
del a[0]
    ''')
    calc_cost('BINARY_LSHIFT','''
a = 1
a = a << 1
    ''')
    calc_cost('BINARY_RSHIFT','''
a = 1
a = a >> 1
    ''')
    calc_cost('BINARY_AND','''
a = 1
a = a & 1
    ''')
    calc_cost('BINARY_XOR','''
a = 1
a = a ^ 1
    ''')
    calc_cost('BINARY_OR','''
a = 1
a = a | 1
    ''')
    calc_cost('INPLACE_POWER','''
a = 1
a **= 1
    ''')
    calc_cost('GET_ITER','''
for a in (1,2): pass
    ''')
    calc_cost('INPLACE_LSHIFT','''
a = 1
a <<= 1
    ''')
    calc_cost('INPLACE_RSHIFT','''
a = 1
a >>= 1
    ''')
    calc_cost('INPLACE_AND','''
a = 1
a &= 1
    ''')
    calc_cost('INPLACE_XOR','''
a = 1
a ^= 1
    ''')
    calc_cost('INPLACE_OR','''
a = 1
a |= 1
    ''')
    calc_cost('BREAK_LOOP','''
for a in (1,2): break
    ''')
    calc_cost('WITH_CLEANUP_START','''
with open("1.txt") as f:
    print(f.read())
    ''')
    calc_cost('WITH_CLEANUP_FINISH','''
with open("1.txt") as f:
    print(f.read())
    ''')
    calc_cost('RETURN_VALUE','''
# empty file
    ''')
    calc_cost('IMPORT_STAR','''
from sys import *
    ''')
    calc_cost('POP_BLOCK','''
for a in (1,2): break
    ''')
    calc_cost('END_FINALLY','''
try:
    a = 1
except ValueError:
    a = 2
finally:
    a = 3
    ''')
    calc_cost('LOAD_BUILD_CLASS','''
class a: pass
    ''')
    calc_cost('STORE_NAME','''
a = 1
    ''')
    calc_cost('DELETE_NAME','''
a = 1
del a
    ''')
    calc_cost('UNPACK_SEQUENCE','''
(a, b) = "ab"
    ''')
    calc_cost('FOR_ITER','''
for i in (1,2): pass
    ''')
    calc_cost('STORE_ATTR','''
import sys
sys.stderr = sys.stdout
    ''')
    calc_cost('DELETE_ATTR','''
import random
random.hello = 'world'
del random.hello
    ''')
    calc_cost('STORE_GLOBAL','''
global a
a = 1
    ''')
    calc_cost('DELETE_GLOBAL','''
global a
a = 2
del a
    ''')
    calc_cost('DUP_TOP_TWO','''
a = 0
b = [0]
b[a] += 1
    ''')
    calc_cost('LOAD_CONST','''
a = 1
    ''')
    calc_cost('LOAD_NAME','''
a = 1
a = a
    ''')
    calc_cost('BUILD_TUPLE','''
a = 1;
a = (a, a)
    ''')
    calc_cost('BUILD_LIST','''
[1,2,3]
    ''')
    calc_cost('BUILD_CONST_KEY_MAP','''
{"a":1,"b":2}
    ''')
    calc_cost('LOAD_ATTR','''
[].sort()
    ''')
    calc_cost('COMPARE_OP','''
a = 1 == 2
    ''')
    calc_cost('IMPORT_NAME','''
import random
    ''')
    calc_cost('IMPORT_FROM','''
from dis import opmap
    ''')
    calc_cost('JUMP_FORWARD','''
if 1 == 2: pass
else: pass
    ''')
    calc_cost('POP_JUMP_IF_FALSE','''
if 1 == 2: pass
else: pass
    ''')
    calc_cost('POP_JUMP_IF_TRUE','''
if not(1 == 2): pass
else: pass
    ''')
    calc_cost('JUMP_ABSOLUTE','''
for i in (1,2): pass
    ''')
    calc_cost('LOAD_GLOBAL','''
global a
a = 1
a = a
    ''')
    calc_cost('CONTINUE_LOOP','''
for x in (1,2):
    try: continue
    except: pass
    ''')
    calc_cost('SETUP_LOOP','''
while 0 > 1: pass
    ''')
    calc_cost('SETUP_EXCEPT','''
try:
    a = 1
except ValueError:
    a = 2
finally:
    a = 3
    ''')
    calc_cost('SETUP_FINALLY','''
try:
    a = 1
except ValueError:
    a = 2
finally:
    a = 3
    ''')
    calc_cost('RAISE_VARARGS','''
raise ValueError
    ''')
    calc_cost('CALL_FUNCTION','''
def f(): pass
f()
    ''')
    calc_cost('MAKE_FUNCTION','''
def f(): pass
    ''')
    calc_cost('BUILD_SLICE','''
a = [1,2,3,4]
b = a[::-1]
    ''')
    calc_cost('CALL_FUNCTION_EX','''
def f(a,b): pass
a = (1,2)
f(*a)
    ''')

def isolate_costs():
    X = []
    y = []
    for opcode, item in costs.items():
        X.append([item['ops'][i] if item['ops'].get(i) else 0 for i in range(143)])
        y.append(item['t'])
    X = np.array(X)
    y = np.array(y)
    avgs = np.array(nnls(X, y)[0])
    
    print('Max time in all instructions: {}s'.format(np.max(avgs)))
    print('Max time in all code snippets: {}s'.format(np.max(y)))

    x = [i for i in range(143) if i in relevant_ops]
    avgs = [avg for idx, avg in enumerate(avgs) if idx in relevant_ops]
    plt.plot(x, avgs, 'o', label='Average Times', markersize=10)
    # plt.plot(x, m*x + c, 'r', label='Fitted line')
    plt.legend()
    plt.show()

if __name__ == '__main__':
    histogram_file = open('opcode.csv', 'w+')
    precalc_costs()
    isolate_costs()
