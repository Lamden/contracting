import sys
from seneca.engine.module import SenecaFinder, RedisFinder
from seneca.engine.interpreter import SenecaInterpreter

class SenecaInterface:

    # Only do this once in each process!
    sys.meta_path = [sys.meta_path[2], SenecaFinder(), RedisFinder()]

    def execute_code_str(self, code_str, scope={}):
        code_obj = self.compile_code(code_str, scope)
        try:
            return SenecaInterpreter.execute(code_obj, scope)
        except:
            SenecaInterpreter.imports = {}
            raise

    def submit_code_str(self, fullname, code_str, keep_original=False):
        try:
            SenecaInterpreter.set_code(fullname, code_str, keep_original)
        except:
            SenecaInterpreter.imports = {}
            raise

    def get_code(self, fullname):
        return SenecaInterpreter.get_code_str(fullname).decode()

    def compile_code(self, code_str, scope={}):
        tree = SenecaInterpreter.parse_ast(code_str, protected_variables=list(scope.keys()))
        return compile(tree, filename='__main__', mode="exec")

    def run_code(self, code_obj, scope):
        try:
            return SenecaInterpreter.execute(code_obj, scope)
        except:
            SenecaInterpreter.imports = {}
            raise
