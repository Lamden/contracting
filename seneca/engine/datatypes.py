import redis
import json

type_to_string = {
    str: 'str',
    int: 'int',
    bool: 'bool',
}


string_to_type = {
    'str': str,
    'int': int,
    'bool': bool
}


def parse_representation(r, delimiter=':'):
    assert type(r) == str
    assert r[0] == delimiter

    components = r[1:].split(delimiter)

    _type = components[0]
    _prefix = components[1]
    _key_type = string_to_type[components[2]]
    _value_type = string_to_type[components[3]]

    if _type == 'map':
        return HMap(_prefix, _key_type, _value_type)


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


class RObject:
    def __init__(self, prefix=None,
                 key_type=str,
                 value_type=int,
                 delimiter=':',
                 rep_str='obj',
                 driver=redis.StrictRedis(host='localhost',
                                          port=6379,
                                          db=0)
                 ):
        assert driver is not None, 'Provide a Redis driver.'
        self.driver = driver

        self.prefix = prefix
        self.key_type = key_type
        self.value_type = value_type

        self.delimiter = delimiter
        self.rep_str = rep_str

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
        try:
            return parse_representation(value.decode())
        except Exception as e:
            if value is not None:
                value = value.decode()
                value = json.loads(value)
            return value

    def check_key_type(self, key):
        assert isinstance(key, self.key_type) or \
               self.key_type is None, \
            'Key {} is not of type "{}"'.format(type(key), self.key_type)

    def rep(self):
        return self.delimiter + self.rep_str \
               + self.delimiter + self.prefix \
               + self.delimiter + type_to_string[self.key_type] \
               + self.delimiter + type_to_string[self.value_type] + self.delimiter


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

    def set(self, key, value):
        v = self.encode_value(value)
        self.check_key_type(key)

        return self.driver.set(self.prefix + self.delimiter + key, v)

    def get(self, key):
        g = self.driver.get(self.prefix + self.delimiter + key)
        g = self.decode_value(g)
        return g

    def __getitem__(self, k):
        return self.get(k)

    def __setitem__(self, k, v):
        return self.set(k, v)


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

        self.p = self.prefix + self.delimiter

    def get(self, i):
        g = self.driver.lindex(self.p, i)
        g = self.decode_value(g)
        return g

    def set(self, i, value):
        #TODO add error handling for trying to set indexes that don't exist
        v = self.encode_value(value)
        return self.driver.lset(self.p, i, v)

    def push(self, value):
        v = self.encode_value(value)
        return self.driver.lpush(self.p, v)

    def pop(self):
        g = self.driver.lpop(self.p)
        g = self.decode_value(g)
        return g

    def pop_right(self):
        g = self.driver.rpop(self.p)
        g = self.decode_value(g)
        return g

    def append(self, value):
        v = self.encode_value(value)
        return self.driver.rpush(self.p, v)

    def extend(self, l):
        for ll in l:
            self.append(ll)

    def __getitem__(self, i):
        return self.get(i)

    def __setitem__(self, i, v):
        return self.set(i, v)

    def rep(self):
        return self.delimiter + self.rep_str \
               + self.delimiter + self.prefix \
               + self.delimiter + type_to_string[self.value_type] + self.delimiter


def hlist(prefix=None, value_type=int):
    if prefix is None:
        return Placeholder(value_type=value_type, placeholder_type=HList)
    return HList(prefix=prefix, value_type=value_type)


####################
# Table Datatype
####################
class Table(RObject):
    def __init__(self, prefix=None, key_type=str, schema=None):
        super().__init__(prefix=prefix,
                         key_type=key_type,
                         value_type=dict,
                         rep_str='table')
        assert self.validate_schema(schema), 'Schema is not the correct type.'
        self.schema = schema
        self.p = self.prefix + self.delimiter

    def validate_schema(self, d):
        for k, v in d.items():
            if not isinstance(k, str):
                return False
            if not isinstance(v, type):
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

        return v

    def set(self, k, v):
        assert self.dict_matches_schema(v)

        for _k, _v in v.items():
            v[_k] = self.encode_value(_v, self.schema[_k])

        self.driver.hmset(self.p + k, v)

    def get(self, k, s=None):
        d = {}

        if s is None:
            keys = tuple(self.schema.keys())
        else:
            keys = s

        result = self.driver.hmget(self.p + k, keys)
        result = [self.decode_value(r) for r in result]

        for i in range(len(keys)):
            d[keys[i]] = result[i]

        return d

    def __getitem__(self, k):
        return self.get(k)

    def __setitem__(self, i, v):
        return self.set(k, v)


class TablePlaceholder(Placeholder):
    def __init__(self, key_type=str, schema=None):
        self.key_type = key_type
        self.schema = schema
        self.placeholder_type = Table

    def valid(self, t):
        mock_table = Table(prefix=None, key_type=self.key_type, schema=self.schema)
        if self.key_type == t.key_type and \
                mock_table.dict_matches_schema(t):
            return True
        return False


def table(prefix=None, key_type=str, schema=None):
    if prefix is None:
        return TablePlaceholder(key_type=key_type, schema=schema)
    return Table(prefix=prefix, key_type=key_type, schema=schema)
