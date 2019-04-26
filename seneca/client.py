from .execution.executor import Executor
from .ast.compiler import SenecaCompiler
from functools import partial
import ast
import inspect
import autopep8

class AbstractContract:
    def __init__(self, name, signer, environment, executor, funcs):
        self.name = name
        self.signer = signer
        self.environment = environment
        self.executor = executor

        # set up virtual functions
        for f in funcs:
            # unpack tuple packed in SenecaClient
            func, kwargs = f

            # set the kwargs to None. these will fail if they are not provided
            default_kwargs = {}
            for kwarg in kwargs:
                default_kwargs[kwarg] = None

            setattr(self, func, partial(self._abstract_function_call,
                                        signer=self.signer,
                                        contract=self.name,
                                        executor=self.executor,
                                        func=func,
                                        environment=self.environment,
                                        **default_kwargs))

    def _abstract_function_call(self, signer, executor, contract, environment, func, **kwargs):
        for k, v in kwargs.items():
            assert v is not None, 'Keyword "{}" not provided. Must not be None.'.format(k)

        status, result = executor.execute(sender=signer,
                                          contract_name=contract,
                                          function_name=func,
                                          kwargs=kwargs,
                                          environment=environment)

        if status == 1:
            raise result

        return result


class SenecaClient:
    def __init__(self, signer='sys', executor=Executor(), compiler=SenecaCompiler()):
        self.executor = executor
        self.raw_driver = self.executor.driver
        self.signer = signer
        self.compiler = compiler

    # Returns abstract contract which has partial methods mapped to each exported function.
    def get_contract(self, name):
        contract = self.raw_driver.get_contract(name)
        tree = ast.parse(contract)

        function_defs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]

        funcs = []
        for definition in function_defs:
            func_name = definition.name
            kwargs = [arg.arg for arg in definition.args.args]

            funcs.append((func_name, kwargs))

        return AbstractContract(name=name,
                                signer=self.signer,
                                environment={},
                                executor=self.executor,
                                funcs=funcs)

    # def submit(self, f, name, bypass=False):
    #     tree = ast.parse(f)
    #
    #     assert isinstance(tree, ast.Module)
    #
    #     parent_func = tree.body[0]
    #
    #     assert isinstance(parent_func, ast.FunctionDef)
    #
    #     tree.body = parent_func.body
    #
    #
    #
    #     standard_indented_code = autopep8.fix_code(code_str, options={'select': ['E101']})
    #
    #     final_code = ''
    #     for line in standard_indented_code.split('\n'):
    #         if line.startswith('    '):
    #             final_code += line[4:] + '\n'
    #
    #     final_code = autopep8.fix_code(final_code)
    #
    #     self.submit_string(final_code, name, bypass)

    def submit_string(self, code_string, name, bypass=False):
        if not bypass:
            self.compiler.parse(code_string, lint=True)

        self.raw_driver.set_contract(name=name, code=code_string)
