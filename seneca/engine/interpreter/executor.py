from seneca.engine.interpreter.parser import Parser
from seneca.engine.interpreter.scope import Scope
from seneca.libs.metering.tracer import Tracer
from seneca.constants.config import MASTER_DB, LEDIS_PORT, CODE_OBJ_MAX_CACHE, OFFICIAL_CONTRACTS, READ_ONLY_MODE
import seneca, sys, marshal, os, types, ujson as json
from base64 import b64encode, b64decode
from os.path import join
from functools import lru_cache
from seneca.engine.interpreter.utils import Plugins, Assert
from seneca.engine.interpreter.module import SenecaFinder, LedisFinder
from seneca.engine.interpreter.driver import Driver
from seneca.engine.book_keeper import BookKeeper
from seneca.engine.conflict_resolution import LedisProxy


class Executor:

    def __init__(self, metering=True, concurrency=True, flushall=False):

        Parser.executor = self
        self.metering = False
        self.concurrency = False
        self.reset_syspath()
        self.driver_base = Driver(host='localhost', port=LEDIS_PORT, db=MASTER_DB)
        self.driver_proxy = None
        if flushall: self.driver.flushall()
        self.path = join(seneca.__path__[0], 'contracts')
        self.author = '324ee2e3544a8853a3c5a0ef0946b929aa488cbe7e7ee31a0fef9585ce398502'
        self.official_contracts = OFFICIAL_CONTRACTS
        self.setup_official_contracts()
        self.metering = metering
        self.concurrency = concurrency
        self.setup_tracer()

    @property
    def driver(self):
        if self.concurrency:
            if not self.driver_proxy:
                info = BookKeeper.get_cr_info()
                self.driver_proxy = LedisProxy(sbb_idx=info['sbb_idx'], contract_idx=info['contract_idx'],
                                               data=info['data'])
            else:
                info = BookKeeper.get_cr_info()
                self.driver_proxy.sbb_idx = info['sbb_idx']
                self.driver_proxy.contract_idx = info['contract_idx']
                self.driver_proxy.data = info['data']
            return self.driver_proxy
        else:
            return self.driver_base

    def reset_syspath(self):
        if not isinstance(sys.meta_path[-1], LedisFinder):
            self.old_sys_path = sys.meta_path
            #self.new_sys_path = [sys.meta_path[-1], SenecaFinder(), LedisFinder()]
            # self.new_sys_path = [*sys.meta_path, SenecaFinder(), LedisFinder()]
            self.new_sys_path = [*sys.meta_path, SenecaFinder(), LedisFinder()]

            sys.meta_path = self.new_sys_path

    def setup_tracer(self):
        seneca_path = seneca.__path__[0]
        path = join(seneca_path, 'constants', 'cu_costs.const')
        os.environ['CU_COST_FNAME'] = path
        self.tracer = Tracer()
        Plugins.submit_stamps()

    def setup_official_contracts(self):
        for name in self.official_contracts:
            if self.driver.hexists('contracts', name):
                continue
            with open(join(self.path, name+'.sen.py')) as f:
                code_str = f.read()
                code_obj, resources, methods = self.compile(name, code_str, {'ast': None, '__system__': True, '__executor__': self})
            self.set_contract(name, **{
                'code_str': code_str,
                'code_obj': code_obj,
                'author': self.author,
                'resources': resources,
                'methods': methods,
            }, driver=self.driver, override=True)

    @lru_cache(maxsize=CODE_OBJ_MAX_CACHE)
    def get_contract(self, contract_name):
        contract = marshal.loads(b64decode(self.driver.hget('contracts', contract_name).decode()))
        return contract

    def set_contract(self, contract_name, code_str, code_obj, author, resources, methods, driver=None, override=False):
        if not driver:
            driver = self.driver
        if not override:
            assert not driver.hget('contracts', contract_name), 'Contract name "{}" already taken.'.format(contract_name)
        sss = b64encode(marshal.dumps({
            'code_str': code_str,
            'code_obj': code_obj,
            'author': author,
            'resources': resources.get(contract_name, {}),
            'methods': methods.get(contract_name, {}),
        }))
        driver.hset('contracts', contract_name, b64encode(marshal.dumps({
            'code_str': code_str,
            'code_obj': code_obj,
            'author': author,
            'resources': resources.get(contract_name, {}),
            'methods': methods.get(contract_name, {}),
        })))


    @staticmethod
    def compile(contract_name, code_str, scope={}):
        Parser.reset()
        Executor.set_default_rt(Parser.parser_scope.get('rt', {}))
        Parser.parser_scope.update(scope)
        Parser.parser_scope['rt']['contract'] = contract_name
        seed_tree = Parser.parse_ast(code_str)
        seed_code_obj = compile(seed_tree, contract_name, 'exec')
        Parser.parser_scope['ast'] = None
        Parser.parser_scope['__system__'] = None
        Parser.parser_scope['__seed__'] = True
        Scope.scope = Parser.parser_scope
        exec(seed_code_obj, Parser.parser_scope)
        Assert.validate(Scope.scope['imports'], Scope.scope['exports'], Scope.scope['resources'], contract_name)
        Parser.parser_scope.update(Scope.scope)  # Scope is updated for seeding purposes!
        return seed_code_obj, Parser.parser_scope['resources'], Parser.parser_scope['methods']

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
    def get_contract_func(self, contract_name, func_name):
        import_path = 'seneca.contracts.{}.{}'.format(contract_name, func_name)
        Assert.valid_import_path(import_path)
        code_str = ''
        try:
            meta = self.get_contract(contract_name)
            author = meta['author']
        except Exception as e:
            author = self.author
        if self.metering:
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
        self.set_default_rt()
        self.compile('__main__', code_str, scope)

    def get_resource(self, contract_name, resource_name):
        meta = self.get_contract(contract_name)
        try:
            exec(meta['code_obj'], Parser.parser_scope)
        except:
            pass
        resource = Parser.parser_scope.get(resource_name)
        resource.contract_name = contract_name
        if not Parser.parser_scope['imports'].get(resource_name):
            Parser.parser_scope['imports'][resource_name] = set()
        Parser.parser_scope['imports'][resource_name].add(contract_name)
        Parser.parser_scope['__safe_execution__'] = False
        resource.access_mode = READ_ONLY_MODE
        if resource.__class__.__name__ == 'Resource':
            resource = resource.resource_obj
        return resource

    def execute_function(self, contract_name, func_name, sender, stamps=0, kwargs={}):
        Parser.parser_scope.update({
            'rt': {
                'sender': sender,
                'origin': sender,
                'contract': contract_name,
                'concurrency': self.concurrency,
                'metering': self.metering
            },
            '__stamps__': stamps,
            '__kwargs__': kwargs,
            '__tracer__': self.tracer,
            '__safe_execution__': True
        })
        Parser.parser_scope.update(Parser.basic_scope)
        current_executor = Parser.executor
        code_obj, author = self.get_contract_func(contract_name, func_name)
        if contract_name in ('smart_contract', ):
            Parser.parser_scope['__executor__'] = self
        else:
            if Parser.parser_scope.get('__executor__'):
                del Parser.parser_scope['__executor__']
        Parser.parser_scope['rt']['author'] = author
        Parser.parser_scope['callstack'] = []

        Scope.scope = Parser.parser_scope
        stamps_used = 0

        if self.metering and not self.tracer.started:
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
                Parser.parser_scope['rt']['contract'] = 'currency'
                exec(Plugins.submit_stamps(), Parser.parser_scope)
                stamps_used = Scope.scope.get('__stamps_used__', 0)
                if error:
                    raise error
        else:
            try:
                exec(code_obj, Scope.scope)
            except Exception as e:
                raise
        Parser.parser_scope.update(Scope.scope)
        Parser.parser_scope['__safe_execution__'] = False
        Parser.executor = current_executor
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

    def dynamic_import(self, contract_name, sender):
        contract = self.get_contract(contract_name)
        module = types.ModuleType(contract_name)
        Parser.parser_scope['rt']['contract'] = contract_name
        Parser.parser_scope['rt']['sender'] = sender
        Parser.parser_scope['__seed__'] = False
        self.execute(contract['code_obj'], module.__dict__)
        return module

