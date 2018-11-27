from seneca.libs.datatypes import hmap

floats = hmap('floats', str, float)

@export
def store_float(s, f):
    floats[s] = f

@export
def read_float(s):
    return floats[s]

@export
def double_float(s):
    print(2 * floats[s])

@export
def add_floats(s1, s2):
    return floats[s1] + floats[s2]
