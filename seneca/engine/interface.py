import sys, importlib, warnings
from seneca.engine.module import SenecaFinder, RedisFinder
from seneca.engine.interpreter import SenecaInterpreter, Seneca
import inspect
import autopep8


class SenecaInterface(SenecaInterpreter):
    """
        High level API for interacting with Seneca Smart Contracts
    """

    def __init__(self, *args, **kwargs):
        if not isinstance(sys.meta_path[2], RedisFinder):
            self.old_sys_path = sys.meta_path
            sys.meta_path = [sys.meta_path[2], SenecaFinder(), RedisFinder()]
        Seneca.interface = self
        super().__init__(*args, **kwargs)

    def __enter__(self, *args, **kwargs):
        self.old_concurrent_mode = Seneca.concurrent_mode
        return self

    def __exit__(self, type, value, traceback):
        Seneca.concurrent_mode = self.old_concurrent_mode
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

    def compile_code(self, code_str, scope={'rt': {'sender': 'anonymous', 'contract': 'arbitrary'}}):
        tree, code, prevalidated = self.parse_ast(code_str, protected_variables=list(scope.keys()))
        prevalidated_obj = compile(prevalidated, filename='__main__', mode="exec")
        self.execute(prevalidated_obj, scope)
        tree_obj = compile(tree, filename='__main__', mode="exec")
        code_obj = compile(code, filename='__main__', mode="exec")
        scope.update({'__seed__': True})
        self.execute(tree_obj, scope)
        return tree_obj, code_obj

    def execute_code_str(self, code_str, scope={'rt': {'sender': 'anonymous', 'contract': 'arbitrary'}}):
        Seneca.imports = {}
        tree_obj, code_obj = self.compile_code(code_str, scope)
        return self.execute(tree_obj, scope)

    def publish_code_str(self, fullname, author, code_str, scope={}):
        assert not self.r.hexists('contracts', fullname), 'Contract "{}" already exists!'.format(fullname)
        Seneca.imports = {}
        tree_obj, code_obj = self.compile_code(code_str, scope={'rt': {'author': author, 'contract': fullname}})
        self.set_code(fullname, tree_obj, code_obj, code_str, author)

    def publish_function(self, f, contract_name, author, scope={}):
        code_str = self.function_to_code_string(f)
        assert not self.r.hexists('contracts', contract_name), 'Contract "{}" already exists!'.format(contract_name)
        Seneca.imports = {}
        tree_obj, code_obj = self.compile_code(code_str, scope={'rt': {'author': author, 'contract': contract_name}})
        self.set_code(fullname=contract_name, tree_obj=tree_obj, code_obj=code_obj, code_str=code_str, author=author)
