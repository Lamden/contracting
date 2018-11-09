import dis, time, os, sys

_ITERATION = 10
_DEBUG = True

def timeit(fn):
    def _fn(*args, **kwargs):

        ### Disable stdout
        if not _DEBUG:
            stdout = sys.stdout
            f = open(os.devnull, 'w')
            sys.stdout = f

        ### Average the cost
        avg = 0
        for i in range(_ITERATION):
            start = time.clock()
            fn(*args, **kwargs)
            end = time.clock()
            avg += end-start
        avg = avg/_ITERATION

        ### Reenable stdout
        if not _DEBUG:
            sys.stdout = stdout
        print('{}s'.format(avg))
        return avg
    return _fn

@timeit
def calc_cost(code_str):
    dis.dis(code_str)

### DEBUG only
calc_cost('''
def f():
    return (lambda:1)()
f()
''')
quit()

################################################################################
#   Start Pre-Calculate Costs
################################################################################

################################################################################

# LOAD STORE
RETURN_VALUE = calc_cost('# empty file') / 2.0
LOAD_CONST = RETURN_VALUE
STORE_NAME = calc_cost('a=1') - 2*LOAD_CONST - RETURN_VALUE
LOAD_NAME = calc_cost('''
a = 1
a = a
''') - 2*LOAD_CONST - 2*STORE_NAME - RETURN_VALUE

# UNARY
_UNARY_COST = 2*LOAD_CONST + 2*STORE_NAME + RETURN_VALUE
UNARY_POSITIVE = calc_cost('''
a = 1
a = +a
''') - _UNARY_COST
UNARY_NEGATIVE = calc_cost('''
a = 1
a = -a
''') - _UNARY_COST
UNARY_NOT = calc_cost('''
a = 1
a = not a
''') - _UNARY_COST
# UNARY_CONVERT = calc_cost('''
# a = 1
# a = `a`
# ''') - _UNARY_COST
UNARY_INVERT = calc_cost('''
a = 1
a = ~a
''') - _UNARY_COST

# ROT
ROT_TWO = calc_cost('''
a = 1; b = 2
(a, b) = (b, a)
''') - 3*LOAD_CONST - 4*STORE_NAME - 2*LOAD_NAME - RETURN_VALUE
ROT_THREE = calc_cost('''
a = 1
(a, a, a) = (a, a, a)
''') - 2*LOAD_CONST - 4*STORE_NAME - 3*LOAD_NAME - RETURN_VALUE
### NOTE ROT_FOUR

# IMPORT
IMPORT_NAME = calc_cost('''
import new
''') - 3*LOAD_CONST - STORE_NAME
IMPORT_FROM = calc_cost('''
from dis import opmap
''') - 3*LOAD_CONST - STORE_NAME - IMPORT_NAME

# FUNCTION
POP_TOP = calc_cost('''
def f(): pass
f()
''') - calc_cost('''
(lambda:1)()
''') - STORE_NAME - LOAD_NAME
MAKE_FUNCTION = calc_cost('''
def f(): pass
''') - 3*LOAD_CONST - STORE_NAME - 2*RETURN_VALUE
CALL_FUNCTION = calc_cost('''
def f(): pass
f()
''') - MAKE_FUNCTION - 3*LOAD_CONST - STORE_NAME - LOAD_NAME - 2*RETURN_VALUE

# BINARY
_BINARY_COST = 3*LOAD_CONST + LOAD_NAME + 2*STORE_NAME + RETURN_VALUE
BINARY_POWER = calc_cost('''
a = 2
a = a ** 2
''') - _BINARY_COST
BINARY_MULTIPLY = calc_cost('''
a = 2
a = a * 2
''') - _BINARY_COST
BINARY_DIVIDE = calc_cost('''
a = 2
a = a / 2
''') - _BINARY_COST
BINARY_MODULO = calc_cost('''
a = 2
a = a % 2
''') - _BINARY_COST
BINARY_ADD = calc_cost('''
a = 2
a = a + 2
''') - _BINARY_COST
BINARY_SUBTRACT = calc_cost('''
a = 2
a = a - 2
''') - _BINARY_COST
BINARY_SUBSCR = calc_cost('''
a = [1]
a[0]
''') - _BINARY_COST
BINARY_FLOOR_DIVIDE = calc_cost('''
a = 2
a = a // 2
''') - _BINARY_COST
BINARY_TRUE_DIVIDE = calc_cost('''
from __future__ import division
a = 2
a = a / 2
''') - _BINARY_COST - IMPORT_FROM - POP_TOP
INPLACE_FLOOR_DIVIDE = calc_cost('''
a = 1
a //= 1
''') - _BINARY_COST
# INPLACE_TRUE_DIVIDE = calc_cost('''
# a = 2
# a = a ** 2
# ''') - _BINARY_COST


################################################################################
#   End Pre-Calculate Costs
################################################################################

import re, copy
g = dict(globals())
for k,v in g.items():
    if re.search(r'^[A-Z][A-Z_]+', k):
        print('{} costs: \n{}s\n'.format(k,v))
