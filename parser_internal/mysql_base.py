'''
Sortable fragments representing parts of an SQL query
'''
from util import auto_set_fields, fst, snd, swap
from enum import Enum
import datetime

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

        NewClass.__name__ = name
        NewClass.__str__ = lambda:name

        return NewClass


sql_python_type_alist = [ ('BIGINT', int),
                          ('VARCHAR', FixedStr),
                          ('TEXT', str),
                          ('DATETIME', datetime.datetime),
                          ('BOOLEAN', bool)
]

valid_mysql_types = list(map(fst, sql_python_type_alist))
supported_python_types = list(map(snd, sql_python_type_alist))
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
    def from_python_type(cls, p_type):
        pass

    def __str__(self):
        if type(self.sql_type) == tuple and self.sql_type[0] =='VARCHAR':
            return '%s(%d)' % (self.sql_type[0], self.sql_type[1])
        else:
            return self.sql_type
