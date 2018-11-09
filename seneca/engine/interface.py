import sys, importlib
from seneca.engine.module import SenecaFinder, RedisFinder
from seneca.engine.interpreter import SenecaInterpreter

class SenecaInterface(SenecaInterpreter):
    """
        High level API for interacting with Seneca Smart Contracts
    """

    def __init__(self, concurrent_mode=True):
        print('init called with con mode: {}'.format(concurrent_mode))
        if not isinstance(sys.meta_path[2], RedisFinder):
            self.old_sys_path = sys.meta_path
            sys.meta_path = [sys.meta_path[2], SenecaFinder(), RedisFinder()]
        SenecaInterpreter.setup(concurrent_mode)
        SenecaInterpreter.concurrent_mode = concurrent_mode

    def __enter__(self, *args, **kwargs):
        self.old_concurrent_mode = SenecaInterpreter.concurrent_mode
        return self

    def __exit__(self, type, value, traceback):
        SenecaInterpreter.concurrent_mode = self.old_concurrent_mode
        return False

    def compile_code(self, code_str, scope={}):
        tree, prevalidated = self.parse_ast(code_str, protected_variables=list(scope.keys()))
        prevalidated_obj = compile(prevalidated, filename='__main__', mode="exec")
        self.execute(prevalidated_obj, scope)
        code_obj = compile(tree, filename='__main__', mode="exec")
        # api = self.construct_api(scope)
        return code_obj

    def construct_api(self, scope):
        for k,v in scope.items():
            if hasattr(v, '__qualname__'):
                if v.__qualname__ == 'Export.__call__.<locals>._fn':
                    print(k, 'xxx')

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
            with SenecaInterface(False) as interface:
                code_obj = self.compile_code(code_str, scope)
                self.set_code(fullname, code_obj, code_str, author, keep_original)
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
