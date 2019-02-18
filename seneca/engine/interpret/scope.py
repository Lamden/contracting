class Scope:

    scope = {}

    def set_scope(self, fn, args, kwargs):


        # Set contract name
        old_contract_name = self.scope['rt']['contract']
        contract_name = fn.__module__ or self.scope['rt']['contract']
        self.scope['rt']['contract'] = contract_name
        self.scope['callstack'].append('{}.{}'.format(contract_name, fn.__name__))

        # Set stamps for currency
        if contract_name and fn.__name__ == 'submit_stamps':
            return (), {'stamps': self.scope['__stamps__']}

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
            export_name = '{}.{}'.format(contract_name, fn.__name__)
            self.scope['exports'][export_name] = True
        return fn


# Run only during compilation
class Seed(Scope):
    def __call__(self, fn):
        if self.scope.get('__seed__'):
            # old_concurrent_mode = Scope.concurrent_mode
            # Scope.concurrent_mode = False
            # BookKeeper.set_info(rt=fn.__globals__['rt'])
            fn()
            # Scope.concurrent_mode = old_concurrent_mode