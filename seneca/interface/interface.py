import sys
from seneca.engine.module import SenecaFinder, RedisFinder
from seneca.engine.interpreter import SenecaInterpreter

class SenecaInterface:

    def __init__(self):
        sys.meta_path = [SenecaFinder(), RedisFinder()]
        self.interpreter = SenecaInterpreter()

    def execute_code_str(self, code_str):
        tree = self.interpreter._parse_ast(code_str)
        code_obj = compile(tree, filename='__main__', mode="exec")
        self.interpreter.execute(code_obj)

    def submit_code_str(self, fullname, code_str, keep_original=False):
        self.interpreter.set_code(fullname, code_str, keep_original)

    def get_code(self, fullname):
        return self.interpreter.get_code_str(fullname).decode()
