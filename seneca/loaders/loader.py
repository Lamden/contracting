import sys

from importlib.abc import Loader, MetaPathFinder
from importlib import invalidate_caches

from redis import Redis

'''
    Is this where interaction with the database occurs with the interface of code strings, etc?
    IE: pushing a contract does sanity checks here?
'''
class Database:
    def __init__(self, host='localhost', port=6379, delimiter=':', db=0, code_key='__code__', type_key='__type__'):
        self.conn = Redis(host=host, port=port, db=db)
        self.delimiter = delimiter
        self.code_key = code_key
        self.type_key = type_key

        # Tests if access to the DB is available
        self.conn.ping()

    def get_contract(self, name):
        return self.conn.hget(name, self.code_key)

    def push_contract(self, name, code, _type='user'):
        d = {
            self.code_key: code,
            self.type_key: _type
        }
        self.conn.hmset(name, d)

    def flush(self):
        self.conn.flushdb()


class DatabaseFinder(MetaPathFinder):
    def find_module(fullname, path, target=None):
        return DatabaseLoader()


class DatabaseLoader(Loader):
    def __init__(self):
        self.d = Database()

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        # fetch the individual contract
        code = self.d.get_contract(module.__name__)
        exec(code, vars(module))

    def module_repr(self, module):
        return '<module {!r} (smart contract)>'.format(module.__name__)


'''
    This module will remain untested and unused until we decide how we want to 'forget' importing.
'''
def uninstall_builtins():
    sys.meta_path.clear()
    sys.path_hooks.clear()
    sys.path.clear()
    sys.path_importer_cache.clear()
    invalidate_caches()


def install_database_loader():
    sys.meta_path.append(DatabaseFinder)


def uninstall_database_loader():
    sys.meta_path.remove(DatabaseFinder)