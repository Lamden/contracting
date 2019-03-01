class Scope:

    scope = {}

    def set_scope(self, fn, args, kwargs):

        # Set contract name
        old_contract_name = self.scope['rt']['contract']
        contract_name = fn.__module__ or self.scope['rt']['contract']
        if len(self.scope['callstack']) == 0 and old_contract_name != '__main__' and contract_name != 'currency':
            contract_name = old_contract_name

        self.scope['rt']['contract'] = contract_name
        self.scope['callstack'].append('{}.{}'.format(contract_name, fn.__name__))

        # Set stamps for currency
        if contract_name == 'currency':
            if fn.__name__ == 'assert_stamps':
                return (), {'stamps': self.scope['__stamps__']}
            elif fn.__name__ == 'submit_stamps':
                return (), {'stamps': self.scope['__stamps_used__']}

        # Set args and kwargs for top level run
        if len(self.scope['callstack']) == 1:
            if self.scope.get('__args__'):
                args = self.scope['__args__']
            if self.scope.get('__kwargs__'):
                kwargs = self.scope['__kwargs__']
        elif contract_name != old_contract_name:
            self.scope['rt']['sender'] = old_contract_name

        fn.__globals__['rt'] = self.scope['rt']

        return args, kwargs

    def reset_scope(self, fn):
        if len(self.scope['callstack']) > 0:
            self.scope['callstack'].pop(0)


# Applies to Private, Export, and Seed functions
class Function(Scope):
    def __call__(self, fn):
        def _fn(*args, **kwargs):
            args, kwargs = self.set_scope(fn, args, kwargs)
            res = fn(*args, **kwargs)
            self.reset_scope(fn)
            return res
        _fn.__name__ = fn.__name__
        fn.__module__ = self.scope['rt']['contract']
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
                if not driver.hexists('contracts', self.scope['rt']['contract']):
                    fn()
            else:
                fn()