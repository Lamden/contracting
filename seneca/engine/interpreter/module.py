import os
from os.path import join, exists, isdir, basename
from importlib.util import spec_from_file_location
from seneca.engine.interpreter.parser import Parser
from seneca.config import SENECA_SC_PATH

import sys

from importlib.abc import Loader, MetaPathFinder
from importlib import invalidate_caches

from seneca.storage.driver import Driver
from seneca.config import DB_URL, DB_PORT, DB_DELIMITER


class SenecaFinder(MetaPathFinder):

    def find_spec(self, fullname, path, target=None):
        if path is None or path == "":
            path = [os.getcwd()] # top level import --
        if fullname.startswith(SENECA_SC_PATH):
            return None
        if "." in fullname:
            *parents, name = fullname.split(".")
        else:
            name = fullname
        for entry in path:
            if isdir(join(entry, name)):
                # this module has child modules
                filename = join(entry, name, "__init__.py")
                if not exists(filename):
                    with open(filename, "w+") as f:
                        pass
                submodule_locations = [join(entry, name)]
            else:
                filename = join(entry, name)
                if exists(filename+'.py'):
                    submodule_locations = [filename]
                    filename += '.py'
                elif exists(filename+'.sen.py'):
                    filename += '.sen.py'
                    submodule_locations = None
                else:
                    continue
            return spec_from_file_location(fullname, filename, loader=SenecaLoader(filename),
                                           submodule_search_locations=submodule_locations)
        return None # we don't know how to import this


class SenecaLoader(Loader):

    def __init__(self, filename):
        self.filename = filename
        self.tree = None
        self.contract_name = basename(filename).split('.')[0]
        with open(self.filename) as f:
            compile_obj = f.read()
            if self.filename.endswith('.sen.py'):
                compile_obj = Parser.parse_ast(compile_obj)
            self.code_obj = compile(compile_obj, filename=self.filename, mode="exec")

    def exec_module(self, module):
        old_contract_name = Parser.parser_scope['rt']['contract']
        Parser.parser_scope['rt']['contract'] = self.contract_name
        scope = vars(module)
        scope.update(Parser.parser_scope)
        Parser.executor.execute(self.code_obj, scope)
        Parser.parser_scope['rt']['contract'] = old_contract_name
        return module


class LedisFinder:

    # raghu todo this is a deprecated method. will work for now according to python docs
    def find_module(self, fullname, path=None):
        if fullname.startswith(SENECA_SC_PATH):
            return LedisLoader(fullname)
        return None


class LedisLoader(SenecaLoader):

    def __init__(self, fullname):
        self.fullname = fullname
        self.contract_name = fullname.split('.')[2]
        self.code_obj = Parser.executor.get_contract(self.contract_name)['code_obj']
        self.is_main = True


'''
    Is this where interaction with the database occurs with the interface of code strings, etc?
    IE: pushing a contract does sanity checks here?
'''
class ContractDriver(Driver):
    def __init__(self, host=DB_URL, port=DB_PORT, delimiter=DB_DELIMITER, db=0, code_key='__code__', type_key='__type__'):
        super().__init__(host=host, port=port, delimiter=delimiter, db=db)

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
        self.d = ContractDriver()

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