class Scope:

    scope = {}

    def set_scope(self, fn, args, kwargs):
        if len(self.scope['callstack']) == 1:
            if self.scope.get('__arguments__'):
                kwargs = self.scope['__arguments__']
        self.scope['callstack'].append('{}.{}'.format(fn.__module__, fn.__name__))
        return kwargs

    def reset_scope(self, fn):
        self.scope['callstack'].pop()


class Function(Scope):
    def __call__(self, fn):
        def _fn(*args, **kwargs):
            kwargs = self.set_scope(fn, args, kwargs)
            res = fn(*args, **kwargs)
            self.reset_scope(fn)
            return res
        return _fn


class Export(Scope):
    def __call__(self, fn):
        def _fn(*args, **kwargs):
            kwargs = self.set_scope(fn, args, kwargs)
            res = fn(*args, **kwargs)
            self.reset_scope(fn)
            return res
        return _fn


class Seed(Scope):
    def __call__(self, fn):
        if fn.__globals__.get('__seed__'):
            # old_concurrent_mode = Scope.concurrent_mode
            # Scope.concurrent_mode = False
            # BookKeeper.set_info(rt=fn.__globals__['rt'])
            fn()
            # Scope.concurrent_mode = old_concurrent_mode