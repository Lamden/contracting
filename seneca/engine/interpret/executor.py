from seneca.engine.interpret.parser import Parser
from seneca.engine.interpret.scope import Scope
from seneca.constants.config import MASTER_DB, REDIS_PORT, CODE_OBJ_MAX_CACHE
import seneca, redis, ujson as json, sys, marshal, os
from os.path import join
from functools import lru_cache
from seneca.engine.interpret.utils import Plugins, Assert
from seneca.engine.interpret.module import SenecaFinder, RedisFinder


class Executor:

    def __init__(self, currency=True, concurrency=True):

        if not isinstance(sys.meta_path[-1], RedisFinder):
            self.old_sys_path = sys.meta_path
            SenecaFinder.executor = self
            sys.meta_path = [sys.meta_path[-1], SenecaFinder(), RedisFinder()]

        self.r = redis.StrictRedis(host='localhost', port=REDIS_PORT, db=MASTER_DB)
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
        Parser.executor = self

    def setup_tracer(self):
        if self.currency:
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
                code_obj, resources, methods = self.compile(name, code_str)
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
        Parser.reset(contract_name)
        Parser.parser_scope['protected'].update(scope.keys())
        seed_tree = Parser.parse_ast(code_str)
        seed_code_obj = compile(seed_tree, contract_name, 'exec')
        exec(seed_code_obj, Parser.parser_scope)
        return seed_code_obj, Parser.parser_scope['resources'], Parser.parser_scope['exports']

    @lru_cache(maxsize=CODE_OBJ_MAX_CACHE)
    def get_contract_cache(self, contract_name, func_name, stamps_supplied=0):
        import_path = 'seneca.contracts.{}.{}'.format(contract_name, func_name)
        Assert.valid_import_path(import_path)
        code_str = ''
        try:
            meta = self.get_contract(contract_name)
            Parser.parser_scope['rt']['author'] = meta['author']
            Parser.parser_scope['__seed__'] = True
            # code_str = meta['code_str']
            exec(meta['code_obj'], Parser.parser_scope)
        except Exception as e:
            Parser.parser_scope['rt']['author'] = self.author
        if self.currency:
            code_str = Plugins.stamps(code_str, stamps_supplied)
        code_str = Plugins.import_module(code_str, contract_name, func_name)
        code_obj = compile(code_str, import_path, 'exec')
        return code_obj

    def execute(self, code_obj, scope={}):
        scope.update(Parser.parser_scope)
        Scope.scope = scope
        exec(code_obj, scope)
        return scope.get('__result__')

    def execute_code_str(self, code_str, scope={}):
        scope.update(Parser.parser_scope)
        code_obj, _, _ = self.compile('__main__', code_str, scope)
        Scope.scope = scope
        exec(code_str, scope)
        return scope.get('__result__')

    def execute_function(self, contract_name, func_name, sender, stamps=0, arguments={}):
        Parser.parser_scope.update({
            'rt': {
                'sender': sender,
                'origin': sender,
                'contract': contract_name
            },
            '__arguments__': arguments,
        })
        Parser.parser_scope.update(Parser.basic_scope)
        if contract_name == 'smart_contract':
            Parser.parser_scope['__executor__'] = self
        code_obj = self.get_contract_cache(contract_name, func_name)
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

if __name__ == '__main__':
    r = redis.StrictRedis(host='localhost', port=REDIS_PORT, db=MASTER_DB)
    r.flushall()
    e = Executor(currency=False, concurrency=False)
    c = e.get_contract('currency')
    sc = e.get_contract('smart_contract')
    res = e.execute_function('currency', 'balance_of', 'fish',
                       arguments={
                           'wallet_id': '324ee2e3544a8853a3c5a0ef0946b929aa488cbe7e7ee31a0fef9585ce398502'
                       })
    print(res)
    code_str = '''
@export
def do_it():
    print('i am dumb')
    '''
    res = e.execute_function('smart_contract', 'submit_contract', 'fish',
                       arguments={
                           'contract_name': 'dumb_contract',
                           'code_str': code_str
                       })
    print(res)
    res = e.execute_function('smart_contract', 'get_contract', 'fish',
                             arguments={
                                 'contract_name': 'dumb_contract'
                             })
    print(res)
    res = e.execute_function('dump_contract', 'do_it', 'fish')
    print(res)
    res = e.execute_function('smart_contract', 'submit_contract', 'fish',
                             arguments={
                                 'contract_name': 'dumb_contract',
                                 'code_str': code_str
                             })
    print(res)
