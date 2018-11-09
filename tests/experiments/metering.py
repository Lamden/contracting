import dis, time

def nop():
    pass

class MutableCodeObject(object):
    args_name = ("co_argcount", "co_kwonlyargcount", "co_nlocals", "co_stacksize", "co_flags", "co_code",
                  "co_consts", "co_names", "co_varnames", "co_filename", "co_name", "co_firstlineno",
                   "co_lnotab", "co_freevars", "co_cellvars")

    def __init__(self, initial_code):
        self.initial_code = initial_code
        for attr_name in self.args_name:
            attr = getattr(self.initial_code, attr_name)
            if isinstance(attr, tuple):
                attr = list(attr)
            setattr(self, attr_name, attr)

    def get_code(self):
        args = []
        for attr_name in self.args_name:
            attr = getattr(self, attr_name)
            if isinstance(attr, list):
                attr = tuple(attr)
            args.append(attr)
        return self.initial_code.__class__(*args)

    @staticmethod
    def print(code):
        dis.show_code(code)
        for ins in dis.get_instructions(code):
            print(ins)

if __name__ == '__main__':

    code = MutableCodeObject(nop.__code__)

    #   1 OPTIMIZED
    #   2 NEWLOCALS
    #   4 VARARGS
    #   8 VARKEYWORDS
    #  16 NESTED
    #  32 GENERATOR
    #  64 NOFREE
    # 128 COROUTINE
    # 256 ITERABLE_COROUTINE

    code.co_consts = (5,)
    code.co_names = ('a',)
    # OPTIMIZED, NEWLOCALS, VARARGS, VARKEYWORDS, NESTED, GENERATOR, NOFREE, COROUTINE, ITERABLE_COROUTINE, ASYNC_GENERATOR
    # code.co_flags = 3
    # code.co_flags = 1000000
    # code.co_code = b'\x64\x00' + b'\x53\x00' # LOAD
    code.co_code = b'\x64\x00' + b'\x5A\x00' + b'\x01\x00' + b'\x53\x00' # LOAD - STORE - POP
    # code.co_code = b'\x01\x00'
    code.co_stacksize = 1

    nop.__code__ = code.get_code()

    MutableCodeObject.print(code)
    # MutableCodeObject.print(nop.__code__)

    # dis.dis(nop)
    # nop()
    # iterations = 10000000
    # start = time.clock()
    # for i in range(iterations):
    #     nop()
    # end = time.clock()
    # print('{}s elapsed'.format(end-start))
    # print('{}s avg'.format((end-start)/iterations))
