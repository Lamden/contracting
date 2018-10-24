import sys
from seneca.engine.module import SenecaFinder, RedisFinder
from seneca.engine.interpreter import SenecaInterpreter

class SenecaInterface:

    # Only do this once in each process!
    sys.meta_path = [sys.meta_path[2], SenecaFinder(), RedisFinder()]

    def execute_code_str(self, code_str, scope={}):
        tree = SenecaInterpreter.parse_ast(code_str, protected_variables=list(scope.keys()))
        code_obj = compile(tree, filename='__main__', mode="exec")
        return SenecaInterpreter.execute(code_obj, scope)

    def submit_code_str(self, fullname, code_str, keep_original=False):
        SenecaInterpreter.set_code(fullname, code_str, keep_original)

    def get_code(self, fullname):
        return SenecaInterpreter.get_code_str(fullname).decode()
