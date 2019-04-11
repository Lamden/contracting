import copy


class Scope:

    scope = {}

    def set_scope(self, fn, args, kwargs):

        # Set contract name

        caller_contract = self.scope['rt']['contract']
        contract_name = fn.__module__ or self.scope['rt']['contract']
        if len(self.scope['callstack']) == 0 and caller_contract != '__main__' and contract_name != 'currency':
            contract_name = caller_contract

        self.scope['rt']['contract'] = contract_name
        caller_rt = copy.deepcopy(self.scope['rt'])
        self.scope['callstack'].append((contract_name, fn, caller_rt))

        # Set stamps for currency
        if contract_name == 'currency':
            if fn.__name__ == 'assert_stamps':
                return (), {'stamps': self.scope['__stamps__']}
            elif fn.__name__ == 'submit_stamps':
                return (), {'stamps': self.scope['__stamps_used__']}

        # Set args and kwargs for top level run
        if len(self.scope['callstack']) == 1:
            if self.scope.get('__kwargs__'):
                kwargs = self.scope['__kwargs__']
        elif contract_name != caller_contract:
            self.scope['rt']['sender'] = caller_contract

        fn.__globals__['rt'] = self.scope['rt']

        return args, kwargs

    def reset_scope(self):
        if len(self.scope['callstack']) > 0:
            self.scope['callstack'].pop(-1)
            if len(self.scope['callstack']) > 0:
                contract_name, fn, caller_rt = self.scope['callstack'][-1]
                fn.__globals__['rt'] = caller_rt


# Applies to Private, Export, and Seed functions
class Function(Scope):
    def __call__(self, fn):

        def _fn(*args, **kwargs):
            contract_name = self.scope['rt']['contract']
            if self.scope['namespace'].get(contract_name, {}).get(fn.__name__):
                new_fn = self.scope['namespace'][contract_name][fn.__name__]
            else:
                new_fn = fn
            args, kwargs = self.set_scope(fn, args, kwargs)
            res = new_fn(*args, **kwargs)
            self.reset_scope()
            return res

        contract_name = self.scope['rt']['contract']
        _fn.__name__ = fn.__name__
        fn.__module__ = contract_name
        self.scope['namespace'][contract_name][fn.__name__] = fn
        self.scope['methods'][contract_name][fn.__name__] = fn.__code__.co_varnames
        return _fn


# Only used during AST parsing
class Export(Scope):
    def __call__(self, fn):
        contract_name = self.scope['rt']['contract']
        if contract_name != '__main__':
            if not self.scope['exports'].get(fn.__name__):
                self.scope['exports'][fn.__name__] = set()
            self.scope['exports'][fn.__name__].add(contract_name)
        return fn


# Run only during compilation
class Seed(Scope):
    def __call__(self, fn):
        if self.scope.get('__seed__'):
            if self.scope.get('__executor__'):
                driver = self.scope['__executor__'].driver
                # if not driver.hexists('contracts', self.scope['rt']['contract']): # TODO change back to this after CR
                if not driver.hget('contracts', self.scope['rt']['contract']):
                    fn()
            else:
                fn()

