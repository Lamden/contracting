import sys

from importlib.abc import Loader, MetaPathFinder
from importlib import invalidate_caches

from ..db.driver import ContractDriver
from ..stdlib import env
from ..execution.runtime import rt

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
    def find_module(fullname, path, target=None):
        return DatabaseLoader()

class DatabaseLoader(Loader):
    def __init__(self):
        from seneca.execution.compiler import SenecaCompiler

        self.d = ContractDriver()
        self.sc = SenecaCompiler()

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        # fetch the individual contract
        code = self.d.get_contract(module.__name__)
        if code is None:
            raise ImportError("Module {} not found".format(module.__name__))

        ctx = ModuleType('context')

        ctx.caller = rt.ctx[-1]
        ctx.this = module.__name__
        ctx.signer = rt.ctx[0]

        # replace this with the new stdlib stuff
        scope = env.gather()
        scope.update({'ctx': ctx})

        rt.ctx.append(module.__name__)
        self.sc.module_name = rt.ctx[-1]

        code_obj = self.sc.compile(code, lint=False)

        # execute the module with the std env and update the module to pass forward
        exec(code_obj, scope)
        vars(module).update(scope)

        rt.ctx.pop()

    def module_repr(self, module):
        return '<module {!r} (smart contract)>'.format(module.__name__)
