from .execution.executor import Executor
from .compilation.compiler import ContractingCompiler
from functools import partial
import ast
import inspect
import astor
import autopep8
from types import FunctionType
import os

from .db.orm import Variable
from .db.orm import Hash


class AbstractContract:
    def __init__(self, name, signer, environment, executor: Executor, funcs):
        self.name = name
        self.signer = signer
        self.environment = environment
        self.executor = executor
        self.functions = funcs

        # set up virtual functions
        for f in funcs:
            # unpack tuple packed in SenecaClient
            func, kwargs = f

            # set the kwargs to None. these will fail if they are not provided
            default_kwargs = {}
            for kwarg in kwargs:
                default_kwargs[kwarg] = None

            # each function is a partial that allows kwarg overloading and overriding
            setattr(self, func, partial(self._abstract_function_call,
                                        signer=self.signer,
                                        contract=self.name,
                                        executor=self.executor,
                                        func=func,
                                        environment=self.environment,
                                        **default_kwargs))

    def keys(self):
        return self.executor.driver.get_contract_keys(self.name)

    # a variable contains a DOT, but no __, and no :
    # a hash contains a DOT, no __, and a :
    # a constant contains __, a DOT, and :

    def __getattr__(self, item):
        try:
            # return the attribute if it exists on the instance
            return self.__getattribute__(item)
        except AttributeError as e:

            # otherwise, attempt to resolve it. full name is contract.item
            fullname = '{}.{}'.format(self.name, item)

            # if the raw name exists, it is a __protected__ or a variable, so prepare for those
            if fullname in self.keys():
                variable = Variable(contract=self.name, name=item)

                # return just the value if it is __protected__ to prevent sets
                if item.startswith('__'):
                    return variable.get()

                # otherwise, return the variable object with allows sets
                return variable

            # otherwise, see if contract.items: has more than one entry
            if len(self.executor.driver.iter(prefix=self.name+'.'+item+':')) > 0:

                # if so, it is a hash. return the hash object
                return Hash(contract=self.name, name=item)

            # otherwise, the attribut does not exist, so throw the error.
            raise e

    def _abstract_function_call(self, signer, executor, contract, environment, func, **kwargs):
        for k, v in kwargs.items():
            assert v is not None, 'Keyword "{}" not provided. Must not be None.'.format(k)

        status, result, stamps = executor.execute(sender=signer,
                                                  contract_name=contract,
                                                  function_name=func,
                                                  kwargs=kwargs,
                                                  environment=environment)

        if executor.production:
            executor.sandbox.terminate()

        if status == 1:
            raise result

        return result


class ContractingClient:
    def __init__(self, signer='sys',
                 submission_filename=os.path.join(os.path.dirname(__file__), 'contracts/submission.s.py'),
                 executor=Executor(),
                 compiler=ContractingCompiler()):

        self.executor = executor
        self.raw_driver = self.executor.driver
        self.signer = signer
        self.compiler = compiler
        self.submission_filename = submission_filename

        # Seed the genesis contracts into the instance
        with open(self.submission_filename) as f:
            contract = f.read()

        self.raw_driver.set_contract(name='submission',
                                     code=contract,
                                     author=self.signer)

        self.raw_driver.commit()

        self.submission_contract = self.get_contract('submission')

    def flush(self):
        # flushes db and resubmits genesis contracts
        self.raw_driver.flush()
        with open(self.submission_filename) as f:
            contract = f.read()

        self.raw_driver.set_contract(name='submission',
                                     code=contract,
                                     author=self.signer)

        self.raw_driver.commit()

        self.submission_contract = self.get_contract('submission')

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

    def closure_to_code_string(self, f):
        closure_code = inspect.getsource(f)
        closure_code = autopep8.fix_code(closure_code)
        closure_tree = ast.parse(closure_code)

        # Remove the enclosing function by swapping out the function def node with its children
        assert len(closure_tree.body) == 1, 'Module has multiple body nodes.'
        assert isinstance(closure_tree.body[0], ast.FunctionDef), 'Function definition not found at root.'

        func_def_body = closure_tree.body[0]
        closure_tree.body = func_def_body.body

        contract_code = astor.to_source(closure_tree)
        name = func_def_body.name

        return contract_code, name

    def lint(self, f, raise_errors=False):
        if isinstance(f, FunctionType):
            f, _ = self.closure_to_code_string(f)

        tree = ast.parse(f)
        violations = self.compiler.linter.check(tree)

        if violations is None:
            return None
        else:
            if raise_errors:
                for v in violations:
                    raise Exception(v)
            else:
                return violations

    def compile(self, f):
        if isinstance(f, FunctionType):
            f, _ = self.closure_to_code_string(f)

        code = self.compiler.parse_to_code(f)
        return code

    def submit(self, f, name=None):
        if isinstance(f, FunctionType):
            f, name = self.closure_to_code_string(f)

        assert name is not None, 'No name provided.'

        self.submission_contract.submit_contract(name=name, code=f)

    def get_contracts(self):
        contracts = []
        for key in self.raw_driver.keys():
            if key.endswith('.__code__'):
                contracts.append(key.strip('.__code__'))
        return contracts
