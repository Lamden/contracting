import sys

from importlib.abc import Loader, MetaPathFinder
from importlib import invalidate_caches

from seneca.db.driver import ContractDriver
from seneca.stdlib import env
from seneca.execution.runtime import rt

from types import ModuleType


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
    def find_module(self, fullname, path=None):
        return DatabaseLoader()


MODULE_CACHE = {}


class DatabaseLoader(Loader):
    def __init__(self):
        self.d = ContractDriver()

    def create_module(self, spec):
        return None

    def exec_module(self, module):

        # fetch the individual contract
        code = MODULE_CACHE.get(module.__name__)

        if MODULE_CACHE.get(module.__name__) is None:
            code = self.d.get_contract(module.__name__)
            MODULE_CACHE[module.__name__] = code

        if code is None:
            raise ImportError("Module {} not found".format(module.__name__))

        ctx = ModuleType('context')

        ctx.caller = rt.ctx[-1]
        ctx.this = module.__name__
        ctx.signer = rt.ctx[0]

        # replace this with the new stdlib stuff
        scope = env.gather()

        # env is set by the executor and allows passing variables into environments such as 'block time',
        # 'block number', etc to allow cilantro -> seneca referencing
        scope.update(rt.env)

        # ctx = _Context()
        scope.update({'ctx': ctx})

        rt.ctx.append(module.__name__)

        # execute the module with the std env and update the module to pass forward
        exec(code, scope)

        #del scope['__builtins__']

        vars(module).update(scope)

        rt.loaded_modules.append(rt.ctx.pop())

    def module_repr(self, module):
        return '<module {!r} (smart contract)>'.format(module.__name__)
