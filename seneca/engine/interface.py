import sys, importlib
from seneca.engine.module import SenecaFinder, RedisFinder
from seneca.engine.interpreter import SenecaInterpreter

class SenecaInterface(SenecaInterpreter):
    """
        High level API for interacting with Seneca Smart Contracts
    """

    def __init__(self):
        super().__init__()
        if not isinstance(sys.meta_path[2], RedisFinder):
            self.old_sys_path = sys.meta_path
            sys.meta_path = [sys.meta_path[2], SenecaFinder(), RedisFinder()]
        self.setup()

    def teardown(self):
        sys.meta_path = self.old_sys_path

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
            SenecaInterpreter.imports = {}
            raise

    def publish_code_str(self, fullname, author, code_str, keep_original=False, scope={}):
        try:
            assert not self.r.hexists('contracts', fullname), 'Contract "{}" already exists!'.format(fullname)
            code_obj = self.compile_code(code_str, scope)
            self.set_code(fullname, code_obj, code_str, author, keep_original)
            concurrent_mode = SenecaInterpreter.concurrent_mode
            SenecaInterpreter.concurrent_mode = False
            self.execute(code_obj, scope)
            SenecaInterpreter.concurrent_mode = concurrent_mode
        except:
            SenecaInterpreter.imports = {}
            raise

    # Already defined
    # def remove_code(self, fullname): pass

    def get_code(self, fullname):
        return self.get_code_str(fullname)

    def run_code(self, code_obj, scope):
        try:
            return self.execute(code_obj, scope)
        except:
            SenecaInterpreter.imports = {}
            raise
