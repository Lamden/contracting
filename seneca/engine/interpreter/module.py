import os
from os.path import join, exists, isdir, basename
from importlib.abc import Loader, MetaPathFinder
from importlib.util import spec_from_file_location
from seneca.engine.interpreter.parser import Parser
from seneca.constants.config import SENECA_SC_PATH


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