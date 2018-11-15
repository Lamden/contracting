import redis
import ujson as json
from seneca.constants.config import get_redis_port, MASTER_DB, DB_OFFSET, get_redis_password
from seneca.libs.logger import get_logger
from seneca.engine.book_keeper import BookKeeper
from seneca.engine.interpreter import SenecaInterpreter
from seneca.engine.conflict_resolution import RedisProxy

'''

Datatype serialization format:

type<prefix>(declaration)

:map(str, int)
:map<coins>(str, int)

:list<todo>(:map(str, int))


'''

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
REDIS_PORT = get_redis_port()
REDIS_PASSWORD = get_redis_password()

def extract_prefix(s):
    prefix = None
    if s[0] == '<':
        prefix_idx_end = s.find('>')
        prefix_s = s[:prefix_idx_end]
        return prefix_s.split(':')[-1], s[1+prefix_idx_end:]
    return None, s

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
    prefix, s = extract_prefix(s)

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
    prefix, s = extract_prefix(s)

    _type = s[1:-1]

    value_type = parse_type_repr(_type)

    if prefix is not None:
        return hlist(prefix=prefix, value_type=value_type)
    return ListPlaceholder(value_type=value_type)


def build_map_from_repr(s):
    slice_idx = s.find('map') + len('map')
    s = s[slice_idx:]

    # check if the prefix has been defined
    prefix, s = extract_prefix(s)

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
    prefix, s = extract_prefix(s)

    types = s.split(',')

    assert len(types) == 2, 'Too many types provided to the map representation string! {}'.format(types)

    key_type = parse_type_repr(types[0][1:])
    value_type = parse_type_repr(types[1][:-1])

    if prefix is not None:
        return ranked(prefix=prefix, key_type=key_type, value_type=value_type)
    return Placeholder(key_type=key_type, value_type=value_type, placeholder_type=Ranked)


class Placeholder:
    def __init__(self, key_type=str, value_type=int, placeholder_type=None):
        assert placeholder_type is not None and type(placeholder_type) == type, 'Provide a type to represent.'
        self.key_type = key_type
        self.value_type = value_type
        self.placeholder_type = placeholder_type

    def valid(self, t):
        if self.key_type == t.key_type and \
                self.value_type == t.value_type and \
                type(t) == self.placeholder_type:
            return True
        return False

    def rep(self):
        return CTP + 'map' + '(' + encode_type(self.key_type) + ',' + encode_type(self.value_type) + ')'


class ListPlaceholder(Placeholder):
    def __init__(self, value_type=int):
        self.key_type = str
        self.value_type = value_type
        self.placeholder_type = HList

    def valid(self, t):
        if self.value_type == t.value_type and type(t) == self.placeholder_type:
            return True
        return False

    def rep(self):
        return CTP + 'list' + '(' + encode_type(self.value_type) + ')'


class TablePlaceholder(Placeholder):
    def __init__(self, key_type=str, schema=None):
        self.key_type = key_type
        self.schema = schema
        self.placeholder_type = Table

    def valid(self, t):
        self_keys = set(self.schema.keys())
        t_keys = set(t.schema.keys())

        if self_keys == t_keys and self.key_type == t.key_type \
                and t.prefix is not None and isinstance(t, Table):
            return True
        return False

    def rep(self):
        d = '({'
        for k, v in self.schema.items():
            d += '{}'.format(k)
            d += ':'
            d += encode_type(v)
            d += ','
        d = d[:-1]
        d += '})'
        return CTP + 'table' + d


class RankedPlaceholder(Placeholder):
    def __init__(self, key_type=str, value_type=int):
        self.key_type = str
        self.value_type = value_type
        self.placeholder_type = Ranked

    def valid(self, t):
        if self.key_type == t.key_type and \
                self.value_type == t.value_type and \
                type(t) == self.placeholder_type:
            return True
        return False

    def rep(self):
        return CTP + 'ranked' + '(' + encode_type(self.key_type) + ',' + encode_type(self.value_type) + ')'


def is_complex_type(v):
    for t in complex_types:
        if (issubclass(type(v), Placeholder) and issubclass(v.placeholder_type, t)) \
                or issubclass(type(v), t):
            return True
    return False


vivified_primitives = {
    int: 0,
    str: '',
    bool: False
}


# table to be done later
def vivify(potential_prefix, t):
    if t in primitive_types:
        return vivified_primitives[t]
    elif issubclass(type(t), Placeholder):
        if t.placeholder_type == HMap:
            return hmap(prefix=potential_prefix, key_type=t.key_type, value_type=t.value_type)
        elif t.placeholder_type == HList:
            return hlist(prefix=potential_prefix, value_type=t.value_type)
        #elif t == Table:
        #    return table(prefix=potential_prefix, key_type=t.key_type, schema=t.schema)
    elif t in complex_types:
        if type(t) == HMap:
            return hmap(prefix=potential_prefix, key_type=t.key_type, value_type=t.value_type)
        elif type(t) == HList:
            return hlist(prefix=potential_prefix, value_type=t.value_type)
        #elif type(t) == Table:
        #    return table(prefix=potential_prefix, key_type=t.key_type, schema=t.schema)
    return None


class RObject:
    def __init__(self, prefix=None, key_type=str, value_type=int, delimiter=':', rep_str='obj',
                 driver=redis.StrictRedis(host='localhost', port=REDIS_PORT, db=MASTER_DB, password=REDIS_PASSWORD)
                 ):
        assert driver is not None, 'Provide a Redis driver.'
        self.contract_id = SenecaInterpreter.loaded['__main__']['rt']['contract']
        self.driver = driver
        self.prefix = prefix
        self.concurrent_mode = SenecaInterpreter.concurrent_mode
        self.key_type = key_type

        assert key_type is not None, 'Key type cannot be None'
        assert key_type in primitive_types or is_complex_type(key_type)

        # prevents you from requiring an RObject instance that has a prefix as a value type
        assert value_type in primitive_types or isinstance(value_type, Placeholder), \
            'You must pass a Placeholder object that does not contain a prefix as a value type. {}'.format(value_type)

        self.value_type = value_type

        self.delimiter = delimiter
        self.rep_str = rep_str

        if self.concurrent_mode:
            assert BookKeeper.has_info(), "No BookKeeping info found for this thread/process with key {}. Was set_info " \
                                          "called on this thread first?".format(BookKeeper._get_key())
            info = BookKeeper.get_info()
            self.driver = RedisProxy(sbb_idx=info['sbb_idx'], contract_idx=info['contract_idx'], data=info['data'])

    def encode_value(self, value):
        v = None

        if issubclass(type(self.value_type), Placeholder):
            assert self.value_type.valid(value) is True, \
                'Value {} is not a matching map'.format(value)
            v = value.rep()

        else:
            assert type(value) == self.value_type or self.value_type is None, \
                'Value is not of type "{}"'.format(self.value_type)
            v = json.dumps(value)

        v = v.encode()
        return v

    def decode_value(self, value):
        '''
        This is where that fun shit goes for 'parsing representation'
        '''
        if value is not None:
            value = value.decode()
            if value[0] == CTP:
                return parse_complex_type_repr(value)
            else:
                value = json.loads(value)
        return value

    def check_key_type(self, key):
        msg = 'Key {} is not of type "{}"'.format(type(key), self.key_type)
        if type(self.key_type) == type:
            assert isinstance(key, self.key_type), msg
        else:
            assert self.key_type.valid(key), msg

    def rep(self):
        raise NotImplementedError

    def drop(self):
        return self.driver.delete(self.prefix)


####################
# HMap Datatype
####################
class HMap(RObject):
    def __init__(self, prefix=None,
                 key_type=str,
                 value_type=int
                 ):
        super().__init__(prefix=prefix,
                         key_type=key_type,
                         value_type=value_type,
                         rep_str='map')

        self.vivification_idx = 0

    def set(self, key, value):
        v = self.encode_value(value)
        self.check_key_type(key)

        if type(key) in complex_types:
            key = key.rep()

        return self.driver.set('{}{}{}'.format(self.prefix, self.delimiter, key), v)

    def get(self, key):
        if type(key) in complex_types:
            key = key.rep()
        g = self.driver.get('{}{}{}'.format(self.prefix, self.delimiter, key))
        g = self.decode_value(g)
        return g

    def __getitem__(self, k):
        item = self.get(k)
        if item is None and self.value_type is not None:
            return vivify('{}.{}'.format(self.prefix, k), self.value_type)
        return item

    def __setitem__(self, k, v):
        return self.set(k, v)

    def rep(self):
        return '{}map<{}:{}>({},{})'.format(CTP,
                                         self.contract_id,
                                         self.prefix,
                                         encode_type(self.key_type),
                                         encode_type(self.value_type))

    def exists(self, k):
        return self.driver.exists(k)

def hmap(prefix=None, key_type=str, value_type=int):
    if prefix is None:
        return Placeholder(key_type=key_type, value_type=value_type, placeholder_type=HMap)
    return HMap(prefix=prefix, key_type=key_type, value_type=value_type)

####################
# HList Datatype
####################
class HList(RObject):
    def __init__(self, prefix=None,
                 value_type=int
                 ):
        super().__init__(prefix=prefix,
                         key_type=str,
                         value_type=value_type,
                         rep_str='list')

    def get(self, i):
        g = self.driver.lindex(self.prefix, i)
        g = self.decode_value(g)
        return g

    def set(self, i, value):
        #TODO add error handling for trying to set indexes that don't exist
        v = self.encode_value(value)
        return self.driver.lset(self.prefix, i, v)

    def push(self, value):
        v = self.encode_value(value)
        return self.driver.lpush(self.prefix, v)

    def pop(self):
        g = self.driver.lpop(self.prefix)
        g = self.decode_value(g)
        return g

    def pop_right(self):
        g = self.driver.rpop(self.prefix)
        g = self.decode_value(g)
        return g

    def append(self, value):
        v = self.encode_value(value)
        return self.driver.rpush(self.prefix, v)

    def extend(self, l):
        for ll in l:
            self.append(ll)

    def __getitem__(self, i):
        item = self.get(i)
        if item is None and self.value_type is not None:
            return vivify('{}.{}'.format(self.prefix, i), self.value_type)
        return item

    def __setitem__(self, i, v):
        return self.set(i, v)

    def rep(self):
        return '{}list<{}:{}>({})'.format(CTP, self.contract_id, self.prefix, encode_type(self.value_type))

    def exists(self, k):
        return self.driver.exists(k)


def hlist(prefix=None, value_type=int):
    if prefix is None:
        return ListPlaceholder(value_type=value_type)
    return HList(prefix=prefix, value_type=value_type)


####################
# Table Datatype
####################
class Table(RObject):
    def __init__(self, prefix=None, key_type=str, schema=None):
        super().__init__(prefix=prefix,
                         key_type=key_type,
                         value_type=str,
                         rep_str='table')
        assert self.validate_schema(schema), 'Schema is not the correct type.'
        self.schema = schema
        self.p = self.prefix + self.delimiter

    def validate_schema(self, d):
        for k, v in d.items():
            if not isinstance(k, str):
                return False
            if not isinstance(v, type) and not isinstance(v, Placeholder):
                return False
        return True

    def dict_matches_schema(self, d):
        schema_set = set(self.schema.keys())
        d_set = set(d.keys())
        assert schema_set > d_set or schema_set == d_set, \
            'Mismatching keys. {} is not in {}'.format(d_set, schema_set)

        for k, v in d.items():
            assert type(v) == self.schema[k], \
                'Mismatching type. {} is not {}'.format(v, self.schema[k])

        return True

    def encode_value(self, value, t):
        v = None

        if issubclass(type(t), Placeholder):
            assert t.valid(value) is True, \
                'Value {} is not a matching map'.format(value)
            v = value.rep()
        else:
            assert type(value) == t or t is None, \
                'Value is not of type "{}"'.format(t)
            v = json.dumps(value)

        v = v.encode()
        return v

    def set(self, k, v):
        assert self.dict_matches_schema(v)
        self.check_key_type(k)

        # modify dictionary in place with encoded values
        for _k, _v in v.items():
            v[_k] = self.encode_value(_v, self.schema[_k])

        if type(k) in complex_types:
            k = k.rep()

        self.driver.hmset('{}{}'.format(self.p, k), v)

    def get(self, k, s=None):
        d = {}

        if s is None:
            keys = tuple(self.schema.keys())
        else:
            keys = s

        if type(k) in complex_types:
            k = k.rep()

        result = self.driver.hmget('{}{}'.format(self.p, k), keys)
        result = [self.decode_value(r) for r in result]

        for i in range(len(keys)):
            d[keys[i]] = result[i]

        return d

    def __getitem__(self, k):
        item = self.get(k)
        if item is None and self.value_type is not None:
            return vivify('{}.{}'.format(self.prefix, k), self.value_type)
        return item

    def __setitem__(self, k, v):
        return self.set(k, v)

    def exists(self, k):
        return self.driver.exists(k)

    def rep(self):
        d = '({'
        for k, v in self.schema.items():
            d += '{}'.format(k)
            d += ':'
            d += encode_type(v)
            d += ','
        d = d[:-1]
        d += '})'
        return CTP + self.rep_str + '<' + self.contract_id + ':' + self.prefix + '>' + d


def table(prefix=None, key_type=str, schema=None):
    if prefix is None:
        return TablePlaceholder(key_type=key_type, schema=schema)
    return Table(prefix=prefix, key_type=key_type, schema=schema)


class Ranked(RObject):
    def __init__(self, prefix=None, key_type=str, value_type=None):
        super().__init__(prefix=prefix,
                         key_type=key_type,
                         value_type=value_type,
                         rep_str='ranked')

    def add(self, member, score: int):
        m = self.encode_value(member)
        return self.driver.zadd(self.prefix, score, m)

    def delete(self, member):
        m = self.encode_value(member)
        return self.driver.zrem(self.prefix, m)

    def get_max(self):
        m = self.driver.zrevrangebyscore(self.prefix, max='+inf', min='-inf', start=0, num=1)
        m = m.pop()
        m = self.decode_value(m)
        return m

    def get_min(self):
        m = self.driver.zrangebyscore(self.prefix, min='-inf', max='+inf', start=0, num=1)
        m = m.pop()
        m = self.decode_value(m)
        return m

    def pop_max(self):
        m = self.get_max()
        return self.delete(m)

    def pop_min(self):
        m = self.get_min()
        return self.delete(m)

    def score(self, member):
        m = self.encode_value(member)
        return self.driver.zscore(self.prefix, m)

    def increment(self, member, i: int):
        m = self.encode_value(member)
        return self.driver.zincrby(self.prefix, m, i)

    def decrement(self, member, i: int):
        i *= -1
        self.increment(member, i)

    def rep(self):
        return '{}ranked<{}:{}>({},{})'.format(CTP,
                                            self.contract_id,
                                            self.prefix,
                                            encode_type(self.key_type),
                                            encode_type(self.value_type))


def ranked(prefix=None, key_type=str, value_type=int):
    if prefix is None:
        return RankedPlaceholder(key_type=key_type, value_type=value_type)
    else:
        return Ranked(prefix=prefix, key_type=key_type, value_type=value_type)


complex_types = [HMap, HList, Table, Ranked]
