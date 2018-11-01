import sys
from seneca.engine.module import SenecaFinder, RedisFinder
from seneca.engine.interpreter import SenecaInterpreter

class SenecaInterface:
    """
        High level API for interacting with Seneca Smart Contracts
    """

    def __init__(self):
        if sys.meta_path[2].__class__.__name__ == 'type':
            sys.meta_path = [sys.meta_path[2], SenecaFinder(), RedisFinder()]

    def compile_code(self, code_str, scope={}):
        tree, prevalidated = SenecaInterpreter.parse_ast(code_str, protected_variables=list(scope.keys()))
        prevalidated_obj = compile(prevalidated, filename='__main__', mode="exec")
        SenecaInterpreter.execute(prevalidated_obj, scope)
        code_obj = compile(tree, filename='__main__', mode="exec")
        return code_obj

    def execute_code_str(self, code_str, scope={}):
        try:
            code_obj = self.compile_code(code_str, scope)
            return SenecaInterpreter.execute(code_obj, scope)
        except:
            SenecaInterpreter.imports = {}
            raise

    def publish_code_str(self, fullname, code_str, keep_original=False, scope={}):
        try:
            assert not SenecaInterpreter.r.hexists('contracts', fullname), 'Contract "{}" already exists!'.format(fullname)
            code_obj = self.compile_code(code_str, scope)
            SenecaInterpreter.set_code(fullname, code_obj, code_str, keep_original)
        except:
            SenecaInterpreter.imports = {}
            raise

    def remove_code(self, fullname):
        SenecaInterpreter.remove_code(fullname)

    def get_code(self, fullname):
        return SenecaInterpreter.get_code_str(fullname).decode()

    def run_code(self, code_obj, scope):
        try:
            return SenecaInterpreter.execute(code_obj, scope)
        except:
            SenecaInterpreter.imports = {}
            raise
