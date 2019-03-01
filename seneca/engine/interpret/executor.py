from seneca.engine.interpret.parser import Parser
from seneca.engine.interpret.scope import Scope
from seneca.libs.metering.tracer import Tracer
from seneca.constants.config import MASTER_DB, REDIS_PORT, CODE_OBJ_MAX_CACHE
import seneca, sys, marshal, os, ast
from os.path import join
from functools import lru_cache
from seneca.engine.interpret.utils import Plugins, Assert
from seneca.engine.interpret.module import SenecaFinder, RedisFinder
from seneca.engine.interpret.driver import Driver


class Executor:

    def __init__(self, currency=True, concurrency=True, flushall=False):

        Parser.executor = self
        self.currency = False
        self.concurrency = False
        self.reset_syspath()
        if flushall: self.driver.flushall()
        self.path = join(seneca.__path__[0], 'contracts')
        self.author = '__lamden_io__'
        self.official_contracts = [
            'currency',
            'smart_contract'
        ]
        self.setup_official_contracts()
        self.currency = currency
        self.concurrency = concurrency
        self.setup_tracer()

    @property
    def driver(self):
        if self.concurrency:
            info = BookKeeper.get_cr_info()
            return RedisProxy(sbb_idx=info['sbb_idx'], contract_idx=info['contract_idx'], data=info['data'])
        else:
            return Driver(host='localhost', port=REDIS_PORT, db=MASTER_DB)

    def reset_syspath(self):
        if not isinstance(sys.meta_path[-1], RedisFinder):
            self.old_sys_path = sys.meta_path
            self.new_sys_path = [sys.meta_path[-1], SenecaFinder(), RedisFinder()]
            sys.meta_path = self.new_sys_path

    def setup_tracer(self):
        seneca_path = seneca.__path__[0]
        path = join(seneca_path, 'constants', 'cu_costs.const')
        os.environ['CU_COST_FNAME'] = path
        self.tracer = Tracer()
        Plugins.submit_stamps()

    def setup_official_contracts(self):
        contracts = {}
        for name in self.official_contracts:
            with open(join(self.path, name+'.sen.py')) as f:
                code_str = f.read()
                code_obj, resources, methods = self.compile(name, code_str, {'ast': '__system__'})
            contracts[name] = {
                'code_str': code_str,
                'code_obj': code_obj,
                'author': self.author,
                'resources': resources,
                'methods': methods,
            }
        for name, c in contracts.items():
            self.set_contract(name, **c, driver=self.driver, override=True)

    def get_contract(self, contract_name):
        return marshal.loads(self.driver.hget('contracts', contract_name))

    def set_contract(self, contract_name, code_str, code_obj, author, resources, methods, driver=None, override=False):
        if not driver:
            driver = self.driver
        if not override:
            assert not driver.hget('contracts', contract_name), 'Contract name "{}" already taken.'.format(contract_name)
        driver.hset('contracts', contract_name, marshal.dumps({
            'code_str': code_str,
            'code_obj': code_obj,
            'author': author,
            'resources': resources,
            'methods': methods,
        }))

    @staticmethod
    def compile(contract_name, code_str, scope={}):
        Parser.reset()
        Executor.set_default_rt(Parser.parser_scope.get('rt', {}))
        Parser.parser_scope.update(scope)
        Parser.parser_scope['protected']['global'].update(scope.keys())
        Parser.parser_scope['rt']['contract'] = contract_name
        seed_tree = Parser.parse_ast(code_str)
        seed_code_obj = compile(seed_tree, contract_name, 'exec')
        Parser.parser_scope['ast'] = None
        Parser.parser_scope['__seed__'] = True
        Scope.scope = Parser.parser_scope
        exec(seed_code_obj, Parser.parser_scope)
        Assert.validate(Scope.scope['imports'], Scope.scope['exports'])
        Parser.parser_scope.update(Scope.scope)  # Scope is updated for seeding purposes!
        return seed_code_obj, Parser.parser_scope['resources'], Parser.parser_scope['exports']

    @staticmethod
    def set_default_rt(rt={}):
        default_rt = {
            'sender': '__main__',
            'origin': '__main__',
            'contract': '__main__'
        }
        default_rt.update(rt)
        Parser.parser_scope['rt'] = default_rt

    @lru_cache(maxsize=CODE_OBJ_MAX_CACHE)
    def get_contract_cache(self, contract_name, func_name):
        import_path = 'seneca.contracts.{}.{}'.format(contract_name, func_name)
        Assert.valid_import_path(import_path)
        code_str = ''
        try:
            meta = self.get_contract(contract_name)
            author = meta['author']
        except Exception as e:
            author = self.author
        if self.currency:
            code_str = Plugins.assert_stamps(code_str)
        code_str = Plugins.import_module(code_str, contract_name, func_name)
        code_obj = compile(code_str, import_path, 'exec')
        return code_obj, author

    def execute(self, code_obj, scope={}):
        scope.update(Parser.parser_scope)
        Scope.scope = scope
        exec(code_obj, scope)
        return scope.get('__result__')

    def execute_code_str(self, code_str, scope={}):
        code_obj, _, _ = self.compile('__main__', code_str, scope)
        scope.update(Parser.basic_scope)
        exec(code_str, scope)
        Parser.parser_scope.update(scope)

    def execute_function(self, contract_name, func_name, sender, stamps=0, args=tuple(), kwargs={}):
        Parser.parser_scope.update({
            'rt': {
                'sender': sender,
                'origin': sender,
                'contract': contract_name
            },
            '__stamps__': stamps,
            '__args__': args,
            '__kwargs__': kwargs,
            '__tracer__': self.tracer,
            '__is_main__': True
        })
        Parser.parser_scope.update(Parser.basic_scope)
        code_obj, author = self.get_contract_cache(contract_name, func_name)
        if contract_name in ('smart_contract', 'dynamic_import'):
            Parser.parser_scope['__executor__'] = self
        else:
            del Parser.parser_scope['__executor__']
        Parser.parser_scope['rt']['author'] = author
        Parser.parser_scope['callstack'] = []
        Scope.scope = Parser.parser_scope
        stamps_used = 0

        if self.currency and not self.tracer.started:
            error = None
            self.tracer.set_stamp(stamps)
            self.tracer.start()
            try:
                exec(code_obj, Parser.parser_scope)
            except Exception as e:
                error = e
            finally:
                # NOTE: Stamp submission is separated from the assertion and execution
                # because we still want to subtract stamps if we run out of stamps.
                self.tracer.stop()
                stamps_used = Scope.scope.get('__stamps_used__', 0)
                exec(Plugins.submit_stamps(), Parser.parser_scope)
                if error:
                    raise error
        else:
            try:
                exec(code_obj, Scope.scope)
            except Exception as e:
                raise
        Parser.parser_scope.update(Scope.scope)
        return {
            'status': 'success',
            'output': Scope.scope.get('__result__'),
            'stamps_used': stamps_used
        }

    def publish_code_str(self, contract_name, author, code_str):
        return self.execute_function('smart_contract', 'submit_contract', author,
                                     kwargs={
                                         'contract_name': contract_name,
                                         'code_str': code_str
                                     })