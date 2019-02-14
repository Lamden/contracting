import sys, os, imp
from os.path import join, exists, isdir, basename
from importlib.abc import Loader, MetaPathFinder
from importlib.util import spec_from_file_location
from seneca.engine.interpret.parser import Parser
from seneca.constants.config import SENECA_SC_PATH


# class SenecaFinder(MetaPathFinder):
#
#     def find_spec(self, fullname, path, target=None):
#         if path is None or path == "":
#             path = [os.getcwd()] # top level import --
#         if "." in fullname:
#             *parents, name = fullname.split(".")
#         else:
#             name = fullname
#         for entry in path:
#             if isdir(join(entry, name)):
#                 # this module has child modules
#                 filename = join(entry, name, "__init__.py")
#                 if not exists(filename): open(filename, "w+")
#                 submodule_locations = [join(entry, name)]
#             else:
#                 filename = join(entry, name)
#                 if exists(filename+'.py'):
#                     submodule_locations = [filename]
#                     filename += '.py'
#                 elif exists(filename+'.sen.py'):
#                     filename += '.sen.py'
#                     submodule_locations = None
#                 else:
#                     continue
#             return spec_from_file_location(fullname, filename, loader=SenecaLoader(filename),
#                                            submodule_search_locations=submodule_locations)
#
#         return None # we don't know how to import this
#
# class SenecaLoader(Loader):
#
#     def __init__(self, filename):
#         self.filename = filename
#         self.tree = None
#         self.module_name = basename(filename).split('.')[0]
#         with open(self.filename) as f:
#             code_str = f.read()
#             if 'seneca/libs' in self.filename:
#                 self.code_obj = compile(code_str, filename=self.filename, mode="exec")
#             else:
#                 self.tree = Parser.parse_ast(code_str)
#                 self.code_obj = compile(self.tree, filename=self.filename, mode="exec")
#
#     def exec_module(self, module):
#         exec(self.code_obj, vars(module))
#         return module
#
# class RedisFinder:
#
#     def find_module(self, fullname, path=None):
#         if fullname.startswith(SENECA_SC_PATH):
#             return RedisLoader()
#         return None
#
#
# class RedisLoader:
#
#     def load_module(self, fullname):
#         self.module_name = module_name = fullname.split('.')[-1]
#         code = Parser.executor.get_contract(module_name)
#         mod = sys.modules.setdefault(fullname, imp.new_module(fullname))
#         mod.__file__ = "<%s>" % self.__class__.__name__
#         mod.__loader__ = self
#         mod.__path__ = []
#         mod.__package__ = fullname
#         exec(code, mod.__dict__)
#         return mod


import os
import encodings.idna, atexit
from os.path import join, exists, isdir, basename
from importlib.abc import Loader, MetaPathFinder
from importlib.util import spec_from_file_location
from seneca.engine.interpret.parser import Parser
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
        self.module_name = basename(filename).split('.')[0]
        with open(self.filename) as f:
            code_str = f.read()
            if 'seneca/libs' in self.filename:
                self.code_obj = compile(code_str, filename=self.filename, mode="exec")
            elif self.filename.endswith('.sen.py'):
                self.tree = Parser.parse_ast(code_str)
                self.code_obj = compile(self.tree, filename=self.filename, mode="exec")


    def exec_module(self, module):
        SenecaFinder.executor.execute(self.code_obj, vars(module))
        return module


class RedisFinder:

    def find_module(self, fullname, path=None):
        if fullname.startswith(SENECA_SC_PATH):
            return RedisLoader(fullname)
        return None


class RedisLoader(Loader):

    def __init__(self, fullname):
        self.fullname = fullname
        self.contract_name = fullname.split('.')[2]
        self.code_obj = SenecaFinder.executor.get_contract(self.contract_name)['code_obj']

    def exec_module(self, module):
        SenecaFinder.executor.execute(self.code_obj)
        return module