import sys

from importlib.abc import Loader, MetaPathFinder
from importlib import invalidate_caches

from seneca.db.driver import ContractDriver
from .runtime import rt


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


def install_system_contracts(directory=''):
    pass


'''
    Is this where interaction with the database occurs with the interface of code strings, etc?
    IE: pushing a contract does sanity checks here?
'''


class DatabaseFinder(MetaPathFinder):
    def find_module(fullname, path, target=None):
        return DatabaseLoader()


class DatabaseLoader(Loader):
    def __init__(self):
        self.d = ContractDriver()

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        # fetch the individual contract
        code = self.d.get_contract(module.__name__)

        caller = rt.ctx[-1]

        module.rt = caller

        rt.ctx.append(module.__name__)
        print('{} added to runtime stack'.format(module.__name__))
        exec(code, vars(module))
        a = rt.ctx.pop()
        print('{} popped from runtime stack'.format(a))

    def module_repr(self, module):
        return '<module {!r} (smart contract)>'.format(module.__name__)


