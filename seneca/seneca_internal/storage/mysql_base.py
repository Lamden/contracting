'''
Utility functions and components to support creation of MySQL queries

def surround(s, x):
    return s + x + s


def in_quotes(x):
    return surround('\'', x)


def in_backticks(x):
    return surround('`', x)

def sql_escapes(s):
    # TODO: make sure everything I need is here.
    import re
    return re.sub("'", "''", s)

'''
from seneca.seneca_internal.util import auto_set_fields, fst, snd, swap
from enum import Enum
import datetime
from terminaltables import AsciiTable
import re
from functools import wraps

from MySQLdb import escape_string as mysql_escape


# Python type factory representing fixed length strings, outputted classes have a set length
class FixedStr(object) :
    def __init__(self):
        raise NotImplementedError("FixedStr shouldn't be called directly, use Len function")

    @classmethod
    def Len(cls, l):
        class NewClass(cls):
            _max_len = l
            name = 'FixedStrLen%d' % l

            def __init__(self, str):
                assert len(str) <= self._max_len
                self.str = str

            def __str__(self):
                return self.str

        NewClass.__name__ = NewClass.name
        NewClass.__str__ = lambda:NewClass.name

        return NewClass


sql_python_type_alist = [ ('BIGINT', int),
                          ('VARCHAR', FixedStr),
                          ('TEXT', str),
                          ('DATETIME', datetime.datetime),
                          ('BOOLEAN', bool),
                          ('DOUBLE', float),
]

valid_mysql_types = [x[0] for x in sql_python_type_alist]
supported_python_types = [x[1] for x in sql_python_type_alist]
mysql_py_dict = dict(sql_python_type_alist)
py_mysql_dict = dict(map(swap, sql_python_type_alist))


class SQLType(object):
    '''This class will create objects representing sql types.'''
    def __init__(self, type_str, *args):
        assert type_str in valid_mysql_types
        if type_str == 'VARCHAR':
            assert len(args) == 1, 'Type VARCHAR requires a length.'
            self.sql_type = ('VARCHAR', args[0])
        else:
            assert not args
            self.sql_type = type_str

    @classmethod
    def from_python_type(cls, python_type):
        if issubclass(python_type, FixedStr):
            return cls('VARCHAR', python_type._max_len)
        else:
            return cls(py_mysql_dict[python_type])

    @classmethod
    def from_db_describe_str(cls, st_str):

        st_str_upper = st_str.upper()
        if st_str_upper in valid_mysql_types:
            return cls(st_str_upper)

        varchar_len = re.search(r'^VARCHAR\((.+)\)$', st_str_upper)
        if varchar_len:
            l = int(varchar_len.group(1))
            return cls('VARCHAR', l)

        if st_str_upper.lower() in ['bigint(20)',
                                    'bigint(20) unsigned',
                                    'bigint(21)',
                                    'bigint(21) unsigned',
            ]:
            return cls('BIGINT')


        raise Exception('Unknown sql type string: ' + st_str)




    def __str__(self):
        if type(self.sql_type) == tuple and self.sql_type[0] =='VARCHAR':
            return '%s(%d)' % (self.sql_type[0], self.sql_type[1])
        else:
            return self.sql_type


def none_handler_decorator(f):
    @wraps(f)
    def wrapper(val):
        if val is None:
            return 'NULL'
        else:
            return f(val)
    return wrapper


def get_py_to_sql_cast_func(py_type):
    casting_func_dict = {
      int: lambda x: str(x),
      float: lambda x: str(x),
      str: lambda x: '\'%s\'' % str(mysql_escape(x), 'utf-8'),
      datetime.datetime: lambda x:'\'%s\'' % x.strftime('%Y-%m-%d %H:%M:%S'),
      bool: lambda x: 'TRUE' if x else 'FALSE',
    }

    casting_func_dict = {k: none_handler_decorator(f) for (k, f) in casting_func_dict.items()}

    if py_type in casting_func_dict.keys():
        return casting_func_dict[py_type]
    elif issubclass(py_type, FixedStr):
        return casting_func_dict[str] # XXX: same casting method to TEXT and to VARCHAR(x)
    elif py_type is type(None): # NOTE: This seems to be the correct way to access NoneType in Python3 :-(
        return lambda _: 'NULL'
    else:
        # TODO: custom exception types
        raise Exception('Unsupported type, cannot convert to SQL str:' + str(py_type))


def cast_py_to_sql(py_val):
    '''Convenience function'''
    return get_py_to_sql_cast_func(type(py_val))(py_val)


def escape_sql_pattern(raw_string):
    # TODO: Make sure this is exhaustive.
    return raw_string.replace('_', '\\_').replace('%', '\\%')

class TabularKVs():
    def __init__(self, keys, rows):
        self.keys = tuple(keys)
        self.key_type = type(keys[0])
        self.record_len = len(keys)
        self.rows = list([self.format_row(x) for x in rows])

    # TODO: def format_keys, should verify no duplicates and all keys are of same type
    # TODO: fast_init method that skips all unecessary steps

    @classmethod
    def from_dicts(cls, ds):
        k0 = list(ds[0].keys())
        tab_kv = cls(k0, [])
        for kv in ds:
            tab_kv.append(kv)
        return tab_kv

    def to_klist_vlists(self):
        return self.keys, self.rows

    def format_row(self, row):
        assert len(row) == self.record_len
        t = type(row)

        if t == tuple:
            return row
        elif t == list:
            return tuple(row)
        elif t == dict:
            return self.row_from_dict(row)
        else:
            raise Exception('Unsupported type.')

    def __len__(self):
        return len(self.rows)

    def __bool__(self):
        return bool(self.__len__())

    # TODO: make a nice efficient __iter__ with an interator
    def __iter__(self):
        return [self.row_to_dict(r) for r in self.rows].__iter__()

    def row_from_dict(self, d):
        assert sorted(d.keys()) == sorted(self.keys)
        return tuple([d[k] for k in self.keys])

    def append(self, v):
        self.rows.append(self.format_row(v))

    def row_to_dict(self, r):
        return dict(zip(self.keys, r))

    # TODO: Decide if the current __repr__ and __str__ are user friendly
    def __str__(self):
        #https://stackoverflow.com/questions/5909873/how-can-i-pretty-print-ascii-tables-with-python
        table_data = [list(self.keys)] + list(map(list, self.rows))
        table = AsciiTable(table_data)
        return table.table

    def __repr__(self):
        return '\n'.join(list([str(self.row_to_dict(x)) for x in self.rows]))

    def __setitem__(self, key, val):
        self.rows[key] = self.format_row(val)

    def __getitem__(self, key):
        return self.row_to_dict(self.rows[key])

    def select(self, *keys):
        indices = [self.keys.index(k) for k in keys]
        return [[r[i] for i in indices] for r in self.rows]


def run_tests():
    tkv = TabularKVs(('a','b','c'), [(1,2,3),(4,5,6)])
    print(tkv)
    print(len(tkv))
    tkv.append((7,8,9))
    print(tkv)
    tkv.append([10,11,12])
    print(tkv)
    tkv.append({'c':15, 'b':14, 'a':13})
    print(tkv)
    print(tkv[0])
    tkv[0] = (101,102,103)
    print(tkv)
    print(tkv.select('a','c'))
