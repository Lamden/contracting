from seneca.engine.interpret.parser import Parser
from seneca.engine.interpret.scope import Scope
from seneca.libs.metering.tracer import Tracer
from seneca.constants.config import MASTER_DB, REDIS_PORT, CODE_OBJ_MAX_CACHE
import seneca, redis, ujson as json, sys, marshal, os
from os.path import join
from functools import lru_cache
from seneca.engine.interpret.utils import Plugins, Assert
from seneca.engine.interpret.module import SenecaFinder, RedisFinder


class Executor:

    def __init__(self, currency=True, concurrency=True, flushall=False):

        Parser.executor = self
        self.reset_syspath()
        self.r = redis.StrictRedis(host='localhost', port=REDIS_PORT, db=MASTER_DB)
        if flushall: self.r.flushall()
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

    def reset_syspath(self):
        if not isinstance(sys.meta_path[-1], RedisFinder):
            self.old_sys_path = sys.meta_path
            # self.new_sys_path = sys.meta_path[-2:] + [SenecaFinder(), RedisFinder()]
            self.new_sys_path = [sys.meta_path[-1], SenecaFinder(), RedisFinder()]
            sys.meta_path = self.new_sys_path

    def setup_tracer(self):
        seneca_path = seneca.__path__[0]
        path = join(seneca_path, 'constants', 'cu_costs.const')
        os.environ['CU_COST_FNAME'] = path
        self.tracer = Tracer()

    def setup_official_contracts(self):
        self.currency = False
        self.concurrency = False
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
        pipe = self.r.pipeline()
        for name, c in contracts.items():
            self.set_contract(name, **c, driver=pipe, override=True)
        pipe.execute()

    def get_contract(self, contract_name):
        return marshal.loads(self.r.hget('contracts', contract_name))

    def set_contract(self, contract_name, code_str, code_obj, author, resources, methods, driver=None, override=False):
        if not driver:
            driver = self.r
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
        Parser.parser_scope['__seed__'] = True
        Scope.scope['ast'] = None
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
            code_str = Plugins.stamps(code_str)
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
            '__kwargs__': kwargs
        })
        Parser.parser_scope.update(Parser.basic_scope)
        code_obj, author = self.get_contract_cache(contract_name, func_name)
        if contract_name == 'smart_contract':
            Parser.parser_scope['__executor__'] = self
        Parser.parser_scope['rt']['author'] = author
        Parser.parser_scope['callstack'] = []
        Scope.scope = Parser.parser_scope

        if self.currency:
            self.tracer.set_stamp(stamps)
            self.tracer.start()
            try:
                exec(code_obj, Parser.parser_scope)
            except Exception as e:
                raise
            finally:
                stamps -= self.tracer.get_stamp_used()
                self.tracer.stop()
        else:
            try:
                exec(code_obj, Scope.scope)
            except Exception as e:
                raise
        Parser.parser_scope.update(Scope.scope)
        return {
            'status': 'success',
            'output': Scope.scope.get('__result__'),
            'remaining_stamps': stamps
        }

    def publish_code_str(self, contract_name, author, code_str):
        return self.execute_function('smart_contract', 'submit_contract', author,
                                     kwargs={
                                         'contract_name': contract_name,
                                         'code_str': code_str
                                     })