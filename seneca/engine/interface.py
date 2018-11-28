import sys, importlib, warnings
from seneca.engine.module import SenecaFinder, RedisFinder
from seneca.engine.interpreter import SenecaInterpreter

class SenecaInterface(SenecaInterpreter):
    """
        High level API for interacting with Seneca Smart Contracts
    """

    def __init__(self, concurrent_mode=True):
        if not isinstance(sys.meta_path[2], RedisFinder):
            self.old_sys_path = sys.meta_path
            sys.meta_path = [sys.meta_path[2], SenecaFinder(), RedisFinder()]
        SenecaInterpreter.setup(concurrent_mode)

    def __enter__(self, *args, **kwargs):
        self.old_concurrent_mode = SenecaInterpreter.concurrent_mode
        return self

    def __exit__(self, type, value, traceback):
        SenecaInterpreter.concurrent_mode = self.old_concurrent_mode
        return False

    def compile_code(self, code_str, scope={}):
        tree, code, prevalidated = self.parse_ast(code_str, protected_variables=list(scope.keys()))
        prevalidated_obj = compile(prevalidated, filename='__main__', mode="exec")
        self.execute(prevalidated_obj, scope)
        tree_obj = compile(tree, filename='__main__', mode="exec")
        code_obj = compile(code, filename='__main__', mode="exec")
        scope.update({'__seed__': True})
        self.execute(tree_obj, scope)
        return tree_obj, code_obj

    def execute_code_str(self, code_str, scope={'rt': {'sender': 'anonymous', 'contract': 'arbitrary'}}):
        SenecaInterpreter.imports = {}
        tree_obj, code_obj = self.compile_code(code_str, scope)
        return self.execute(tree_obj, scope)

    def publish_code_str(self, fullname, author, code_str, scope={}):
        assert not self.r.hexists('contracts', fullname), 'Contract "{}" already exists!'.format(fullname)
        with SenecaInterface(False) as interface:
            SenecaInterpreter.imports = {}
            tree_obj, code_obj = self.compile_code(code_str, scope={'rt': {'author': author, 'contract': fullname}})
            self.set_code(fullname, tree_obj, code_obj, code_str, author)
