import redis


# The maximum idle time (in milisecond) in any moment during the communication with the destination db when copying
# key values. See docs on https://redis.io/commands/migrate for more info


def copy_key(key, new_key, source_db, destination_db, replace=False):
    s_info, d_info = source_db.connection_pool.connection_kwargs, destination_db.connection_pool.connection_kwargs

    # source_db.execute_command('MIGRATE', d_info['host'], d_info['port'], key, d_info['db'], COPY_TIMEOUT, "COPY")
    value = source_db.dump(key)
    destination_db.restore(new_key, 0, value, replace=replace)


r1 = redis.StrictRedis(host='localhost', port=6379, db=0)
r2 = redis.StrictRedis(host='localhost', port=6379, db=1)

r1.flushdb()
r2.flushdb()

K1 = 'MR_OLD_KEY'
K2 = 'MR_NEW_KEY'

DATA = {'k1': 'v1', 'k2': 'v2'}
ALL_KEYS = list(DATA.keys())

assert not r1.exists(K1), "key already exists on r1!"
assert not r2.exists(K1), "key already exists on r2!"

r1.hmset(K1, DATA)
print("Just set data on database 1...hmget returns: {}".format(r1.hmget(K1, ALL_KEYS)))

print("About to copy to new name...")
copy_key(K1, K2, r1, r1)
print("Copy done!")


# print("r2.hmget: {}".format(r2.hmget(K1, ALL_KEYS)))
print("r1.hmget for {}: {}".format(r1.hmget(K1, ALL_KEYS), K1))
print("r1.hmget for {}: {}".format(r1.hmget(K2, ALL_KEYS), K2))
