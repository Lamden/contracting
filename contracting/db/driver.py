from contracting.db.encoder import encode, decode, encode_kv
from contracting.execution.runtime import rt
from contracting.stdlib.bridge.time import Datetime
from contracting.stdlib.bridge.decimal import ContractingDecimal
from contracting import config
from datetime import datetime
import marshal
import decimal
import requests
import pymongo
import os
from pathlib import Path
import shutil
import hashlib
import lmdb
import motor.motor_asyncio
import asyncio

FILE_EXT = '.d'
HASH_EXT = '.x'

STORAGE_HOME = Path().home().joinpath('.lamden')

# DB maps bytes to bytes
# Driver maps string to python object
CODE_KEY = '__code__'
TYPE_KEY = '__type__'
AUTHOR_KEY = '__author__'
OWNER_KEY = '__owner__'
TIME_KEY = '__submitted__'
COMPILED_KEY = '__compiled__'
DEVELOPER_KEY = '__developer__'


class Driver:
    def __init__(self, db='lamden', collection='state'):
        self.client = pymongo.MongoClient()
        self.db = self.client[db][collection]

    def get(self, item: str):
        v = self.db.find_one({'_id': item})

        if v is None:
            return None

        return decode(v['v'])

    def set(self, key, value):
        if value is None:
            self.__delitem__(key)
        else:
            v = encode(value)
            self.db.update_one({'_id': key}, {'$set': {'v': v}}, upsert=True, )

    def flush(self):
        self.db.drop()

    def delete(self, key: str):
        self.__delitem__(key)

    def iter(self, prefix: str, length=0):
        cur = self.db.find({'_id': {'$regex': f'^{prefix}'}})

        keys = []
        for entry in cur:
            keys.append(entry['_id'])
            if 0 < length <= len(keys):
                break

        keys.sort()
        return keys

    def keys(self):
        k = []
        for entry in self.db.find({}):
            k.append(entry['_id'])
        k.sort()
        return k

    def __getitem__(self, item: str):
        value = self.get(item)
        if value is None:
            raise KeyError
        return value

    def __setitem__(self, key: str, value):
        self.set(key, value)

    def __delitem__(self, key: str):
        self.db.delete_one({'_id': key})


class AsyncDriver:
    def __init__(self, db='lamden', collection='state'):
        self.client = motor.motor_asyncio.AsyncIOMotorClient()
        self.db = self.client[db][collection]

    async def get(self, item: str):
        v = await self.db.find_one({'_id': item})

        if v is None:
            return None

        return decode(v['v'])

    async def set(self, key, value):
        if value is None:
            await self.db.delete_one({'_id': key})
        else:
            v = encode(value)
            await self.db.update_one({'_id': key}, {'$set': {'v': v}}, upsert=True, )

    async def flush(self):
        await self.db.drop()

    async def delete(self, key: str):
        await self.db.delete_one({'_id': key})

    async def iter(self, prefix: str, length=0):
        keys = []
        async for entry in self.db.find({'_id': {'$regex': f'^{prefix}'}}):
            keys.append(entry['_id'])
            if 0 < length <= len(keys):
                break

        keys.sort()
        return keys

    async def keys(self):
        k = []
        async for entry in self.db.find({}):
            k.append(entry['_id'])
        k.sort()
        return k

    def __getitem__(self, item: str):
        loop = asyncio.get_event_loop()
        value = loop.run_until_complete(self.get(item))

        if value is None:
            raise KeyError
        return value

    def __setitem__(self, key: str, value):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.set(key, value))

    def __delitem__(self, key: str):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.db.delete_one({'_id': key}))


class InMemDriver(Driver):
    def __init__(self):
        super().__init__()
        self.db = {}

    def get(self, item):
        key = item.encode()
        value = self.db.get(key)
        return decode(value)

    def set(self, key: str, value):
        k = key.encode()
        if value is None:
            self.__delitem__(key)
        else:
            v = encode(value).encode()
            self.db[k] = v

    def delete(self, key: str):
        self.__delitem__(key)

    def iter(self, prefix: str, length=0):
        p = prefix.encode()

        l = []
        for k in sorted(self.db.keys()):
            if k.startswith(p):
                l.append(k.decode())
            if 0 < length <= len(l):
                break

        return l

    def keys(self):
        return sorted([k.decode() for k in self.db.keys()])

    def flush(self):
        self.db.clear()

    def __getitem__(self, item: str):
        value = self.get(item)
        if value is None:
            raise KeyError
        return value

    def __setitem__(self, key: str, value):
        self.set(key, value)

    def __delitem__(self, key: str):
        k = key.encode()
        try:
            del self.db[k]
        except KeyError:
            pass


class FSDriver:
    OS_KEY_LIMIT = (256 - 1) - len(FILE_EXT)

    def __init__(self, root='fs'):
        self.root = os.path.join(Path.home(), root)

    def get(self, item: str):
        try:
            filename = self._key_to_file(item)
            with open(filename, 'r') as f:
                v = f.read()

        except FileNotFoundError:
            return None

        return decode(v)

    def set(self, key, value):
        if value is None:
            self.__delitem__(key)
        else:
            v = encode(value)
            filename = self._key_to_file(key)

            os.makedirs(filename.parents[0], exist_ok=True)

            with open(filename, 'w') as f:
                f.write(v)

    def flush(self):
        try:
            shutil.rmtree(self.root)
        except FileNotFoundError:
            pass

    def delete(self, key: str):
        self.__delitem__(key)

    def iter(self, prefix: str='', length=0):
        keys = []

        for (r, dirs, files) in sorted(os.walk(self.root, topdown=True)):
            files.sort()
            base = r[len(self.root):]

            for f in files:
                if f.endswith(FILE_EXT) and f.startswith(prefix):
                    keys.append(self.path_to_key(os.path.join(base, f)))

                if 0 < length <= len(keys):
                    break

            if 0 < length <= len(keys):
                break

        keys.sort()

        return keys

    def _iter(self, prefix: str='', length=0):
        keys = []

        for (r, dirs, files) in os.walk(os.path.join(self.root, prefix), topdown=True):
            base = r[len(self.root):]

            for f in files:
                if f.endswith(FILE_EXT):
                    keys.append(self.path_to_key(os.path.join(base, f)))

                if 0 < length <= len(keys):
                    break

            if 0 < length <= len(keys):
                break

        keys.sort()

        return keys

    def keys(self):
        return self.iter()

    def __getitem__(self, item: str):
        value = self.get(item)
        if value is None:
            raise KeyError
        return value

    def __setitem__(self, key: str, value):
        self.set(key, value)

    def __delitem__(self, key: str):
        filename = self._key_to_file(key)
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass

    @staticmethod
    def hash_key(key: str):
        h = hashlib.sha3_256()
        h.update(key.encode())

        return h.hexdigest()[:-2] + HASH_EXT

    def _key_to_file(self, key: str):
        filename = key.replace(':', '/')
        filename = filename.replace('.', '/')
        filename += FILE_EXT
        filename = os.path.join(self.root, filename)
        return Path(filename)

    def path_to_key(self, path):
        if path.endswith(FILE_EXT):
            path = path[:-len(FILE_EXT)]

        pth = path.split('/')

        pth = [p for p in pth if p != '']

        contract = pth.pop(0)

        if len(pth) == 0:
            return contract

        variable = pth.pop(0)

        key = '.'.join((contract, variable))

        if len(pth) == 0:
            return key

        key = ':'.join((key, *pth))

        return key


class LMDBDriver:
    def __init__(self, filename=STORAGE_HOME.joinpath('state')):
        self.filename = filename
        self.filename.mkdir(exist_ok=True, parents=True)

        self.db_writer = lmdb.open(path=str(self.filename), map_size=int(1e12), readonly=False)
        self.db_reader = lmdb.open(path=str(self.filename), map_size=int(1e12), readonly=True, lock=False)

    def get(self, item: str):
        with self.db_reader.begin() as tx:
            v = tx.get(item.encode())

        if v is None:
            return None

        return decode(v)

    def set(self, key, value):
        if value is None:
            self.__delitem__(key)
        else:
            v = encode(value)
            with self.db_writer.begin(write=True) as tx:
                tx.put(key.encode(), v.encode())

    def flush(self):
        with self.db_writer.begin(write=True) as tx:
            cursor = tx.cursor()
            for key, _ in cursor:
                tx.delete(key)

    def delete(self, key: str):
        self.__delitem__(key)

    def iter(self, prefix: str, length=0):
        keys = []

        with self.db_reader.begin() as tx:
            cursor = tx.cursor()

            if not cursor.set_range(prefix.encode()):
                return []

            else:
                for key, _ in cursor:
                    if not key.startswith(prefix.encode()):
                        break

                    keys.append(key.decode())

                    if len(keys) >= length > 0:
                        break

        return keys

    def keys(self):
        keys = []

        with self.db_reader.begin() as tx:
            cursor = tx.cursor()
            for key, _ in cursor:
                keys.append(key.decode())

        return keys

    def __getitem__(self, item: str):
        value = self.get(item)
        if value is None:
            raise KeyError
        return value

    def __setitem__(self, key: str, value):
        self.set(key, value)

    def __delitem__(self, key: str):
        with self.db_writer.begin(write=True) as tx:
            tx.delete(key.encode())


class WebDriver(InMemDriver):
    def __init__(self, masternode='http://masternode-01.lamden.io'):
        super().__init__()
        self.masternode = masternode

    def get(self, item: str):
        # supports item strings like contract.variable:key1:key2

        contract, args = item.split('.')
        args = args.split(':')
        variable = args.pop(0)

        keys = ','.join(args)

        r = requests.get(f'{self.masternode}/contracts/{contract}/{variable}?key={keys}')
        return decode(r.json()['value'])


class CacheDriver:
    def __init__(self, driver: Driver=Driver()):
        self.driver = driver
        self.cache = {}

        self.reads = set()
        self.pending_writes = {}

        self.pending_deltas = {}

    def soft_apply(self, hcl: str, state_changes: dict):
        deltas = {}

        for k, v in state_changes.items():
            current = self.get(k)
            deltas[k] = (current, v)

            self.set(k, v)

        self.pending_deltas[hcl] = deltas

    def get(self, key: str, mark=True):
        # Try to get from cache
        v = self.cache.get(key)
        if v is not None:
            rt.deduct_read(*encode_kv(key, v))
            return v

        # If it doesn't exist, get from db, add to cache
        dv = self.driver.get(key)
        rt.deduct_read(*encode_kv(key, dv))

        self.cache[key] = dv

        # Add key to reads
        if mark:
            self.reads.add(key)

        return dv

    def set(self, key, value, mark=True):
        rt.deduct_write(*encode_kv(key, value))

        if type(value) == decimal.Decimal or type(value) == float:
            value = ContractingDecimal(str(value))

        self.cache[key] = value
        if mark:
            self.pending_writes[key] = value

    def delete(self, key, mark=True):
        self.set(key, None, mark=mark)

    def commit(self):
        for k, v in self.pending_writes.items():
            if v is None:
                self.driver.delete(k)
            else:
                self.driver.set(k, v)

    def hard_apply(self, hlc):
        # see if the HCL even exists
        if self.pending_deltas.get(hlc) is None:
            return

        # Run through the sorted HCLs from oldest to newest applying each one until the hcl committed is

        to_delete = []
        for _hlc, _deltas in sorted(self.pending_deltas.items()):

            # Run through all state changes, taking the second value, which is the post delta
            for key, delta in _deltas.items():
                self.driver.set(key, delta[1])

                try:
                    self.cache.pop(key)
                except KeyError:
                    pass

            # Add the key (
            to_delete.append(_hlc)
            if _hlc == hlc:
                break

        # Remove the deltas from the set
        [self.pending_deltas.pop(key) for key in to_delete]

    def rollback(self):
        # Run through the state changes in reverse, reversing the newest to the oldest
        for _hlc, _deltas in reversed(sorted(self.pending_deltas.items())):
            # Run through all state changes, taking the first value, which is the pre delta
            for key, delta in _deltas.items():
                self.set(key, delta[0])

        self.pending_deltas.clear()

    def clear_pending_state(self):
        self.cache.clear()
        self.reads.clear()
        self.pending_writes.clear()


class ContractDriver(CacheDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.delimiter = '.'

    def items(self, prefix=''):
        # Get all of the items in the cache currently
        _items = {}
        keys = set()
        for k, v in self.cache.items():
            if k.startswith(prefix) and v is not None:
                _items[k] = v
                keys.add(k)

        # Get all of the keys we need
        db_keys = set(self.driver.iter(prefix=prefix))

        # Subtract the already gotten keys
        for k in db_keys - keys:
            _items[k] = self.get(k) # Cache get will add the keys to the cache

        return _items

    def keys(self, prefix=''):
        return list(self.items(prefix).keys())

    def values(self, prefix=''):
        return list(self.items(prefix).values())

    def make_key(self, contract, variable, args=[]):
        contract_variable = self.delimiter.join((contract, variable))
        if args:
            return ':'.join((contract_variable, *[str(arg) for arg in args]))
        return contract_variable

    def get_var(self, contract, variable, arguments=[], mark=True):
        key = self.make_key(contract, variable, arguments)
        return self.get(key, mark=mark)

    def set_var(self, contract, variable, arguments=[], value=None, mark=True):
        key = self.make_key(contract, variable, arguments)
        self.set(key, value, mark=mark)

    def get_contract(self, name):
        return self.get_var(name, CODE_KEY)

    def get_owner(self, name):
        owner = self.get_var(name, OWNER_KEY)
        if owner == '':
            owner = None
        return owner

    def get_time_submitted(self, name):
        return self.get_var(name, TIME_KEY)

    def get_compiled(self, name):
        return self.get_var(name, COMPILED_KEY)

    def set_contract(self, name, code, owner=None, overwrite=False, timestamp=Datetime._from_datetime(datetime.now()), developer=None):
        if self.get_contract(name) is None:
            code_obj = compile(code, '', 'exec')
            code_blob = marshal.dumps(code_obj)

            self.set_var(name, CODE_KEY, value=code)
            self.set_var(name, COMPILED_KEY, value=code_blob)
            self.set_var(name, OWNER_KEY, value=owner)
            self.set_var(name, TIME_KEY, value=timestamp)
            self.set_var(name, DEVELOPER_KEY, value=developer)

    def delete_contract(self, name):
        for key in self.keys(name):
            if self.cache.get(key) is not None:
                del self.cache[key]

            if self.pending_writes.get(key) is not None:
                del self.pending_writes[key]

            self.driver.delete(key)

    def flush(self):
        self.driver.flush()
        self.clear_pending_state()

    def get_contract_keys(self, name):
        return self.keys(name)

    # Set cache to None
    # Set pending writes to none
    # def delete(self, key):
    #     # if self.cache.get(key) is not None:
    #     #     del self.cache[key]
    #     #
    #     # if self.pending_writes.get(key) is not None:
    #     #     del self.pending_writes[key]
    #     #
    #     # self.driver.delete(key)
    #     self.cache[key] = None
    #     self.pending_writes[key] = None


class AsyncContractDriver:
    def __init__(self, driver: AsyncDriver):
        self.driver = driver

    async def items(self, prefix=''):
        # Get all of the items in the cache currently
        _items = {}
        keys = set()
        for k, v in self.cache.items():
            if k.startswith(prefix) and v is not None:
                _items[k] = v
                keys.add(k)

        # Get all of the keys we need
        a = await self.driver.iter(prefix=prefix)
        db_keys = set(a)

        # Subtract the already gotten keys
        for k in db_keys - keys:
            _items[k] = self.get(k) # Cache get will add the keys to the cache

        return _items

    async def keys(self, prefix=''):
        items = await self.items(prefix)
        return list(items.keys())

    async def values(self, prefix=''):
        items = await self.items(prefix)
        return list(items.values())

    def make_key(self, contract, variable, args=[]):
        contract_variable = self.delimiter.join((contract, variable))
        if args:
            return ':'.join((contract_variable, *[str(arg) for arg in args]))
        return contract_variable

    def get_var(self, contract, variable, arguments=[], mark=True):
        key = self.make_key(contract, variable, arguments)
        return self.get(key, mark=mark)

    def get_contract(self, name):
        return self.get_var(name, CODE_KEY)

    def get_owner(self, name):
        owner = self.get_var(name, OWNER_KEY)
        if owner == '':
            owner = None
        return owner

    def get_time_submitted(self, name):
        return self.get_var(name, TIME_KEY)

    def get_compiled(self, name):
        return self.get_var(name, COMPILED_KEY)

    def get_contract_keys(self, name):
        return self.keys(name)

    # Set cache to None
    # Set pending writes to none
    # def delete(self, key):
    #     # if self.cache.get(key) is not None:
    #     #     del self.cache[key]
    #     #
    #     # if self.pending_writes.get(key) is not None:
    #     #     del self.pending_writes[key]
    #     #
    #     # self.driver.delete(key)
    #     self.cache[key] = None
    #     self.pending_writes[key] = None


class BlockserviceDriver(Driver):
    # conn_str see https://www.mongodb.com/docs/manual/reference/connection-string/
    def __init__(self, conn_str="mongodb://localhost:27017", db='lamden', collection='currentState'):
        self.client = pymongo.MongoClient(conn_str)
        self.db = self.client[db][collection]

    def get(self, item: str):
        v = self.db.find_one({'rawKey': item})
        if v is None:
            return None

        if isinstance(v['value'], dict):
            return decode(encode(v['value']))
        
        if isinstance(v['value'], int):
            return v['value']
        
        if isinstance(v['value'], list):
            return v['value']
        
        try:
            res = decode(v['value'])
            if res is None:
                return v['value']
            return res
        except Exception as e:
            logging.exception(e)
            return v['value']

    def set(self, key, value):
        # Do nothing to keep readonly.
        pass

    def iter(self, prefix: str, length=0):
        cur = self.db.find({'rawKey': {'$regex': f'^{prefix}'}})

        keys = []
        for entry in cur:
            keys.append(entry['rawKey'])
            if 0 < length <= len(keys):
                break

        keys.sort()
        return keys

    def keys(self):
        k = []
        for entry in self.db.find({}):
            k.append(entry['rawKey'])
        k.sort()
        return k

    def __delitem__(self, key: str):
        # Do nothing to keep readonly.
        pass
    
    def flush(self):
        # Do nothing to keep readonly.
        pass