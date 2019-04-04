import sys

from importlib.abc import Loader, MetaPathFinder
from importlib import invalidate_caches

from redis import Redis


class Database:
    def __init__(self, host='localhost', port=6379, delimiter=':'):
        self.conn = Redis(host=host, port=port)
        self.delimiter = delimiter

    def get_contract(self, name):
        return self.conn.hget(name, 'code').decode()


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


def uninstall_builtins():
    sys.meta_path.clear()
    sys.path_hooks.clear()
    sys.path.clear()
    sys.path_importer_cache.clear()
    invalidate_caches()


def install_database_loader():
    sys.meta_path.append(DatabaseFinder)
