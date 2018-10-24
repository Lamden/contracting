import sys
from seneca.engine.module import SenecaFinder, RedisFinder
from seneca.engine.interpreter import SenecaInterpreter

class SenecaInterface:

    def __init__(self):
        sys.meta_path = [SenecaFinder(), RedisFinder()]

    def execute_code_str(self, code_str, scope={}):
        tree = SenecaInterpreter.parse_ast(code_str)
        code_obj = compile(tree, filename='__main__', mode="exec")
        return SenecaInterpreter.execute(code_obj, scope)

    def submit_code_str(self, fullname, code_str, keep_original=False):
        SenecaInterpreter.set_code(fullname, code_str, keep_original)

    def get_code(self, fullname):
        return SenecaInterpreter.get_code_str(fullname).decode()
