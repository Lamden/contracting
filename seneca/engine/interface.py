import sys
from seneca.engine.module import SenecaFinder, RedisFinder
from seneca.engine.interpreter import SenecaInterpreter

class SenecaInterface(SenecaInterpreter):
    """
        High level API for interacting with Seneca Smart Contracts
    """

    def __init__(self):
        sys.meta_path = [sys.meta_path[2], SenecaFinder(), RedisFinder()]

    def compile_code(self, code_str, scope={}):
        tree, prevalidated = self.parse_ast(code_str, protected_variables=list(scope.keys()))
        prevalidated_obj = compile(prevalidated, filename='__main__', mode="exec")
        self.execute(prevalidated_obj, scope)
        code_obj = compile(tree, filename='__main__', mode="exec")
        return code_obj

    def execute_code_str(self, code_str, scope={}):
        try:
            code_obj = self.compile_code(code_str, scope)
            return self.execute(code_obj, scope)
        except:
            self.imports = {}
            raise

    def publish_code_str(self, fullname, code_str, keep_original=False, scope={}):
        try:
            assert not self.r.hexists('contracts', fullname), 'Contract "{}" already exists!'.format(fullname)
            code_obj = self.compile_code(code_str, scope)
            self.set_code(fullname, code_obj, code_str, scope['author'], keep_original)
        except:
            self.imports = {}
            raise

    # Already defined
    # def remove_code(self, fullname): pass

    def get_code(self, fullname):
        return self.get_code_str(fullname).decode()

    def run_code(self, code_obj, scope):
        try:
            return self.execute(code_obj, scope)
        except:
            self.imports = {}
            raise
