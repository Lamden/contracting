"""
Note: Not threadsafe

This Redisnap backend stores data in Python objects. It can be used as a
standalone backend, but it's primarily designed to be used inside the
transactional backend.

TODO: Convert camelcase to snake.
TODO: Add type annotations to everything.
TODO: If there are enough type check of existing values, just change to
decorator.

TODO: Custom exception types, important!

"""
from seneca.engine.storage.redisnap.commands import *
import seneca.engine.storage.redisnap.resp_types as rtype
from seneca.engine.storage.redisnap.backend_abc import ExecuterBase as abc_executer


class Executer(abc_executer):
    """
    >>> e = ExecuterBase(); print(e)
    ExecuterBase({})
    """

    def __init__(self):
        self.data = {}

    def __repr__(self):
        return 'ExecuterBase(%s)' % str(self.data)

    def purge(self):
        self.data = {}

    def exists(self, cmd):
        return cmd.key in self.data

    def type(self, cmd):
        t = type(self.get(Get(cmd.key)))
        if t in [RScalarInt, RScalarFloat]:
            return RScalar

        return t

    def asserttype(self, cmd):
        return isinstance(self.get(cmd), cmd.r_type)

    def get(self, cmd):
        try:
            ret = self.data[cmd.key]
            assert isinstance(ret, RScalar), 'FSR we got the wrong type!'
            return ret
        except KeyError:
            return RDoesNotExist()

    def setnr(self, cmd):
        self.data[cmd.key] = make_rscalar(cmd.value)


    def del_(self, cmd):
        self.data.pop(cmd.key)

    def incrbynr(self, cmd):
        old = self(Get(cmd.key))
        old_type = type(old)

        if issubclass(old_type, RDoesNotExist):
            self(SetNR(cmd.key, cmd.amount))
        elif issubclass(old_type, RScalarInt):
            old.value += cmd.amount
        else:
            raise RedisVauleTypeError('Existing value has wrong type.')

    def appendnr(self, cmd):
        old = self(Get(cmd.key))
        old_type = type(old)
        assert isinstance(old, RScalar)

        if issubclass(old_type, RDoesNotExist):
            self(SetNR(cmd.key, cmd.value))
        elif issubclass(old_type, RScalarInt) or issubclass(old_type, RScalarFloat):
            self(SetNR(cmd.key, str(old.value) + cmd.value))
        elif issubclass(old_type, RScalar):
            old.value += cmd.value
        else:
            raise Exception('Existing value has wrong type.')

    def hget(self, cmd):
        try:
            maybe_rhash = self.data[cmd.key]
            if isinstance(maybe_rhash, RHash):
                return maybe_rhash.data[cmd.field]
            else:
                # TODO: custom exception type
                raise RedisKeyTypeError('Existing value has wrong type.')
        except KeyError:
            return RDoesNotExist()

    def hsetnr(self, cmd):
        if cmd.key in self.data:
            old_val = self.data[cmd.key]
            if not isinstance(old_val, RHash):
                raise RedisKeyTypeError('Existing value has wrong type.')
            else:
                inner_dict = self.data[cmd.key].data
                inner_dict[cmd.field] = make_rscalar(cmd.value)
        else:
            self.data[cmd.key] = RHash({cmd.field: make_rscalar(cmd.value)})

    def hexists(self, cmd):

        try:
            maybe_rhash = self.data[cmd.key]
            if isinstance(maybe_rhash, RHash):
                return cmd.field in maybe_rhash.data
            else:
                raise RedisKeyTypeError('Existing value has wrong type.')
        except KeyError:
            return False

    def lindex(self, cmd):
        try:
            maybe_rlist = self.data[cmd.key]
            if isinstance(maybe_rlist, RList):
                if len(maybe_rlist.data) <= cmd.index:
                     return RDoesNotExist()
                else:
                    return maybe_rlist.data[cmd.index]
            else:
                raise RedisKeyTypeError('Existing value has wrong type.')
        except KeyError:
            return RDoesNotExist()

    def lset(self, cmd):
        try:
            maybe_rlist = self.data[cmd.key]
            if isinstance(maybe_rlist, RList):
                if len(maybe_rlist.data) <= cmd.index:
                    raise RedisListOutOfRange('Index out of range.')
                maybe_rlist.data[cmd.index] = cmd.value
            else:
                raise RedisKeyTypeError('Existing value has wrong type.')
        except KeyError:
            raise RedisKeyTypeError('Cannot LSet an nonexistent key.')

    def _push_nr_base(self, method_name, key, values):
        if key in self.data:
            old_val = self.data[key]
            if not isinstance(old_val, RList):
                raise RedisKeyTypeError('Existing value has wrong type.')
            else:
                getattr(old_val.data, method_name)(*map(make_rscalar, values))
        else:
            self.data[key] = RList(list(map(make_rscalar, values)))

    def lpushnr(self, cmd):
        return self._push_nr_base('appendleft', cmd.key, cmd.value[::-1])

    def rpushnr(self, cmd):
        return self._push_nr_base('append', cmd.key, cmd.value)

    def _pop_base(self, method_name, cmd):
        try:
            maybe_rlist = self.data[cmd.key]
            if isinstance(maybe_rlist, RList):
                if not maybe_rlist.data:
                    raise Exception("Inconsistent state: should never have an empty RList, panic!")
                if len(maybe_rlist.data) == 1:
                    # Redis deletes lists on last pop
                    self.data.pop(cmd.key)
                    return maybe_rlist.data[0]
                else:
                    return getattr(maybe_rlist.data, method_name)()
            else:
                # TODO: custom exception type
                raise RedisKeyTypeError('Existing value has wrong type.')
        except KeyError:
            return RDoesNotExist()


    def lpop(self, cmd):
        return self._pop_base('popleft', cmd)


    def rpop(self, cmd):
        return self._pop_base('pop', cmd)


    def zaddnr(self, cmd):
        if cmd.key in self.data:
            existing_sset = self.data[cmd.key]
            if not isinstance(existing_sset, RSortedSet):
                raise RedisKeyTypeError('Existing value has wrong type.')
            else:
                for m, s in cmd.members_and_scores.items():
                    existing_sset.add(s, m)
        else:
            self.data[cmd.key] = RSortedSet(list(map(swap, cmd.members_and_scores.items())))

    def zremnr(self, cmd):
        if cmd.key in self.data:
            existing_sset = self.data[cmd.key]
            if not isinstance(existing_sset, RSortedSet):
                raise RedisKeyTypeError('Existing value has wrong type.')
            else:
                for m in cmd.members:
                    existing_sset.rem(m)
                if not existing_sset:
                    self.data.pop(cmd.key)
        else:
            pass

    def zrevrangebyscore(self, cmd):
        if cmd.key in self.data:
            existing_sset = self.data[cmd.key]
            if not isinstance(existing_sset, RSortedSet):
                raise RedisKeyTypeError('Existing value has wrong type.')
            else:
                return existing_sset.rev_range_by_score(cmd.max, cmd.min, cmd.inclusive, cmd.with_scores)
        else:
            return []


    def zscore(self, cmd):
        if cmd.key in self.data:
            existing_sset = self.data[cmd.key]
            if not isinstance(existing_sset, RSortedSet):
                raise RedisKeyTypeError('Existing value has wrong type.')
            else:
                try:
                    return existing_sset.score(cmd.member)
                except KeyError as e:
                    return None
        else:
            return None


    def zincrbynr(self, cmd):
        if cmd.key in self.data:
            existing_sset = self.data[cmd.key]
            if not isinstance(existing_sset, RSortedSet):
                raise RedisKeyTypeError('Existing value has wrong type.')
            else:
                if cmd.member in existing_sset:
                    existing_sset.incr_by(cmd.amount, cmd.member)
                else:
                    existing_sset.add(cmd.amount, cmd.member)
        else:
            self.data[cmd.key] = RSortedSet([(cmd.amount, cmd.member)])


    def __call__(self, cmd):
        # TODO: Make sure this is efficient and generally okay.
        if isinstance(cmd, Del):
            return self.del_(cmd)
        return getattr(self, cmd.__class__.__name__.lower())(cmd)

    def contains_command_addr(self, cmd):
        """
        >>> ex.purge()
        >>> ex.contains_command_addr(Get('foo'))
        False
        >>> ex.contains_command_addr(HGet('foo', 'bar'))
        False

        >>> ex(SetNR('foo', 'bar'))
        >>> ex.contains_command_addr(Get('foo'))
        True

        >>> return_exception_tuple(ex.contains_command_addr, HGet('foo', 'bar'))
        ('RedisKeyTypeError', 'Existing value has wrong type.')

        >>> ex(Del('foo'))
        >>> ex(HSetNR('foo', 'bar', 'baz'))

        >>> ex.contains_command_addr(HGet('foo', 'bar'))
        True
        """
        if hasattr(cmd, 'field'):
            return self.hexists(cmd)
        else:
            return self.exists(cmd)


def run_tests(deps_provider):
    ex = Executer()
    from seneca.engine.util import return_exception_tuple

    import doctest, sys
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
