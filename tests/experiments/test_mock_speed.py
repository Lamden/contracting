from unittest.mock import Mock
import time


NUM = 10 ** 5

def _ignore(*args, **kwargs):
    pass

class SuperMock:
    def __getattr__(self, item):
        return _ignore


class Test:
    def some_call(self):
        pass

def build_mocks():
    for _ in range(NUM):
        m = SuperMock()
        m.some_call()
        m.some_call()
        m.some_call()
        m.some_call()
        m.some_call()
        m.some_call()
        m.some_call()

def build_dicts():
    for _ in range(NUM):
        m = Test()
        m.some_call()
        m.some_call()
        m.some_call()
        m.some_call()
        m.some_call()
        m.some_call()
        m.some_call()


print("Mock speed:")
start = time.clock()
build_mocks()
end = time.clock()
print("mock speed: {}".format(end-start))
s1 = end-start

print("Dict speed:")
start = time.clock()
build_dicts()
end = time.clock()
s2 = end-start
print("dict speed: {}".format(end-start))

print("ratio: {}".format(s1/s2))
