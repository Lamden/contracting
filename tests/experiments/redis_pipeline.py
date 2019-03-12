import ledis
from ledis import WatchError


r = ledis.Ledis(host='localhost', port=6379, db=0)
r.flushall()
key = 'hello'
values = ['world', 'there']

with r.pipeline() as pipe:
    pipe.watch(key)
    pipe.multi()
    while len(values):
        try:
            value = values.pop()
            print(value)
            pipe.set(key, value)
        except WatchError:
            print('encountered error')
            pipe.reset()
    pipe.execute()