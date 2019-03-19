from seneca.libs.logger import get_logger
import ledis
from multiprocessing import Process

KEY = 'that_key'
LIST = 'that_list'
COUNT = 10 ** 5


def do_that(proc_name, total_procs):
    num_resets = 0
    r = ledis.Ledis(host='127.0.0.1', db=0, password='')

    for _ in range(COUNT):
        r.incr(KEY)
        if r.get(KEY) == total_procs:
            num_resets += 1
            r.set(KEY, 0)
            r.rpush(LIST, proc_name)

    print("proc {} has {} resets".format(proc_name, num_resets))


def test_incr():
    print("starting incr...")
    r = ledis.Ledis(host='127.0.0.1', db=0, password='')
    for _ in range(COUNT):
        r.incr(KEY)


if __name__ == '__main__':
    r = ledis.Ledis(host='127.0.0.1', db=0, password='')
    r.set(KEY, 0)

    x = 8
    procs = []
    for _ in range(x):
        p = Process(target=test_incr)
        procs.append(p)
        p.start()

    print("joining incrs")
    for p in procs:
        p.join()

    print('expected: ', x * COUNT)
    print('actual: ', r.get(KEY))
