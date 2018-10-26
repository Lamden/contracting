COMPLEX_TYPE_PREFIX = '*'
CTP = COMPLEX_TYPE_PREFIX

# # # CLEAN THIS UP! GOOD LORD!!!
type_to_string = {
    str: 'str',
    int: 'int',
    bool: 'bool',
    bytes: 'bytes'
}


string_to_type = {
    'str': str,
    'int': int,
    'bool': bool,
    'bytes': bytes
}

primitive_types = [int, str, bool, bytes, None]

def encode_type(t):
    if isinstance(t, RObject):
        return t.rep()
    if isinstance(t, Placeholder):
        return t.rep()
    for i in range(len(primitive_types)-1):
        if t == primitive_types[i]:
            return primitive_tokens[i]
    return None


primitive_tokens = ['int', 'str', 'bool', 'bytes']
complex_tokens = ['map', 'list', 'table', 'ranked']
all_tokens = ['int', 'str', 'bool', 'bytes', 'map', 'list', 'table', 'ranked']
# # #

def parse_representation(s):
    if s[0] == CTP:
        return parse_complex_type_repr(s)
    else:
        return parse_simple_type_repr(s)


def parse_type_repr(s):
    if s in complex_tokens:
        return parse_complex_type_repr(s)
    elif s in primitive_tokens:
        return parse_simple_type_repr(s)
    return None


def parse_complex_type_repr(s):
    assert s[0] == CTP
    s = s[1:]
    for t in complex_tokens:
        if s.startswith(t):
            if t == 'table':
                return build_table_from_repr(s)
            elif t == 'list':
                return build_list_from_repr(s)
            elif t == 'map':
                return build_map_from_repr(s)
            elif t == 'ranked':
                return build_ranked_from_repr(s)


def parse_simple_type_repr(s):
    if s == 'str':
        return str
    if s == 'int':
        return int
    if s == 'bool':
        return bool
    if s == 'bytes':
        return bytes


def build_table_from_repr(s):
    t = {}

    slice_idx = s.find('table') + len('table')
    s = s[slice_idx:]

    # check if the prefix has been defined
    prefix = None
    if s[0] == '<':
        prefix_idx_end = s.find('>')
        prefix = s[1:prefix_idx_end]
        s = s[1 + prefix_idx_end:]

    start = s.find('({') + 2
    end = s.find('})')

    s = s[start:end]

    while len(s) > 0:

        key_end = s.find(':')
        key = s[:key_end]

        s = s[key_end:]

        # whichever index is lower is the next value
        # hi:int, ...
        # hi:map(str, ...
        next_simple_type = s.find(',')
        next_complex_type = s.find('(')

        true_next_type = next_simple_type if next_simple_type < next_complex_type else next_complex_type

        if next_simple_type < next_complex_type:
            value = s[1:true_next_type]
            t[key] = parse_simple_type_repr(value)
            s = s[1 + true_next_type:]

        else:
            value_idx_end = s.find(')', next_complex_type)
            value = s[1:value_idx_end + 1]
            t[key] = parse_complex_type_repr(value)
            s = s[1 + value_idx_end + 1:]

    if prefix is not None:
        return table(prefix=prefix, schema=t)
    return TablePlaceholder(schema=t)


def build_list_from_repr(s):
    slice_idx = s.find('list') + len('list')
    s = s[slice_idx:]

    # check if the prefix has been defined
    prefix = None
    if s[0] == '<':
        prefix_idx_end = s.find('>')
        prefix = s[1:prefix_idx_end]
        s = s[1 + prefix_idx_end:]

    _type = s[1:-1]

    value_type = parse_type_repr(_type)

    if prefix is not None:
        return hlist(prefix=prefix, value_type=value_type)
    return ListPlaceholder(value_type=value_type)


def build_map_from_repr(s):
    slice_idx = s.find('map') + len('map')
    s = s[slice_idx:]

    # check if the prefix has been defined
    prefix = None
    if s[0] == '<':
        prefix_idx_end = s.find('>')
        prefix = s[1:prefix_idx_end]
        s = s[1 + prefix_idx_end:]

    types = s.split(',')

    assert len(types) == 2, 'Too many types provided to the map representation string! {}'.format(types)

    key_type = parse_type_repr(types[0][1:])
    value_type = parse_type_repr(types[1][:-1])

    if prefix is not None:
        return hmap(prefix=prefix, key_type=key_type, value_type=value_type)
    return Placeholder(key_type=key_type, value_type=value_type, placeholder_type=HMap)


def build_ranked_from_repr(s):
    slice_idx = s.find('ranked') + len('ranked')
    s = s[slice_idx:]

    # check if the prefix has been defined
    prefix = None
    if s[0] == '<':
        prefix_idx_end = s.find('>')
        prefix = s[1:prefix_idx_end]
        s = s[1 + prefix_idx_end:]

    types = s.split(',')

    assert len(types) == 2, 'Too many types provided to the map representation string! {}'.format(types)

    key_type = parse_type_repr(types[0][1:])
    value_type = parse_type_repr(types[1][:-1])

    if prefix is not None:
        return ranked(prefix=prefix, key_type=key_type, value_type=value_type)
    return Placeholder(key_type=key_type, value_type=value_type, placeholder_type=Ranked)
