import sys, importlib, warnings
from seneca.engine.module import SenecaFinder, RedisFinder
from seneca.engine.interpreter import SenecaInterpreter
import inspect
import autopep8


class SenecaInterface(SenecaInterpreter):
    """
        High level API for interacting with Seneca Smart Contracts
    """

    def __init__(self, concurrent_mode=True, port=None, password=None):
        if not isinstance(sys.meta_path[2], RedisFinder):
            self.old_sys_path = sys.meta_path
            sys.meta_path = [sys.meta_path[2], SenecaFinder(), RedisFinder()]
        SenecaInterpreter.setup(concurrent_mode=concurrent_mode,
                                port=port,
                                password=password)

    def __enter__(self, *args, **kwargs):
        self.old_concurrent_mode = SenecaInterpreter.concurrent_mode
        return self

    def __exit__(self, type, value, traceback):
        SenecaInterpreter.concurrent_mode = self.old_concurrent_mode
        return False

    @staticmethod
    def function_to_code_string(f):
        _code = inspect.getsourcelines(f)[0]
        _code = _code[1:]
        code_str = ''
        for c in _code:
            code_str += c

        standard_indented_code = autopep8.fix_code(code_str, options={'select': ['E101']})

        final_code = ''
        for line in standard_indented_code.split('\n'):
            if line.startswith('    '):
                final_code += line[4:] + '\n'

        final_code = autopep8.fix_code(final_code)

        return final_code

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

    def publish_function(self, f, contract_name, author, scope={}):
        code_str = self.function_to_code_string(f)
        assert not self.r.hexists('contracts', contract_name), 'Contract "{}" already exists!'.format(contract_name)
        code_obj = self.compile_code(code_str, scope={'rt': {'author': author, 'contract': contract_name}})
        self.set_code(contract_name, code_obj, code_str, author)
