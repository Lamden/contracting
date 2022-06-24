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
from contracting.db.hdf5 import h5
import logging

FILE_EXT = '.d'
HASH_EXT = '.x'

STORAGE_HOME = Path().home().joinpath('.lamden')
FSDRIVER_HOME = STORAGE_HOME.joinpath('state')

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

    def get(self, item: str):
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
    def __init__(self, root=FSDRIVER_HOME):
        self.root = root
        self.root.mkdir(exist_ok=True, parents=True)

    def __parse_key(self, key):
        try:
            filename, variable = key.split(config.INDEX_SEPARATOR, 1)
            variable = variable.replace(config.DELIMITER, h5.GROUP_SEPARATOR)
        except:
            filename = '__misc'
            variable = key.replace(config.DELIMITER, h5.GROUP_SEPARATOR)

        return filename, variable

    def __filename_to_path(self, filename):
        return str(self.root.joinpath(filename))

    def __get_files(self):
        return sorted(os.listdir(self.root))

    def __get_keys_from_file(self, filename):
        return [filename + config.INDEX_SEPARATOR + g.replace(h5.GROUP_SEPARATOR, config.DELIMITER) for g in h5.get_groups(self.__filename_to_path(filename))]

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __delitem__(self, key):
        self.delete(key)

    def get(self, item: str):
        filename, variable = self.__parse_key(item)

        return h5.get_value(self.__filename_to_path(filename), variable)

    def set(self, key, value):
        filename, variable = self.__parse_key(key)
        h5.set_value(self.__filename_to_path(filename), variable, value)

    def flush(self):
        try:
            shutil.rmtree(self.root)
            self.root.mkdir(exist_ok=True, parents=True)
        except FileNotFoundError:
            pass

    def delete(self, key):
        filename, variable = self.__parse_key(key)
        h5.del_value(self.__filename_to_path(filename), variable)

    def iter(self, prefix='', length=0):
        keys = []
        for filename in self.__get_files():
            if filename.startswith(prefix):
                keys.extend(self.__get_keys_from_file(filename))
            if length > 0 and len(keys) >= length:
                break

        return keys if length == 0 else keys[:length]

    def keys(self):
        return self.iter()

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
    def __init__(self, driver=None):
        self.pending_writes = {}             # L2 cache
        self.cache = {}                      # L1 cache
        self.driver = driver or FSDriver()   # L0 cache

        self.pending_reads = {}

        self.pending_deltas = {}

    def find(self, key: str):
        value = self.pending_writes.get(key)
        if value is not None:
            return value

        value = self.cache.get(key)
        if value is not None:
            return value

        value = self.driver.get(key)
        if value is not None:
            return value

        return None

    def get(self, key: str, save: bool = True):

        value = self.find(key)

        if save:
            if self.pending_reads.get(key) is None:
                self.pending_reads[key] = value

            if value is not None:
                rt.deduct_read(*encode_kv(key, value))

        return value

    def set(self, key, value):
        rt.deduct_write(*encode_kv(key, value))

        if self.pending_reads.get(key) is None:
            self.get(key)

        if type(value) == decimal.Decimal or type(value) == float:
            value = ContractingDecimal(str(value))

        self.pending_writes[key] = value

    def delete(self, key):
        self.set(key, None)

    #TODO: Fix bug where rolling back on a key written to twice rolls back to the initial state instead of the immediate previous value
    def soft_apply(self, hcl: str):
        deltas = {}

        for k, v in self.pending_writes.items():
            current = self.pending_reads.get(k)
            deltas[k] = (current, v)

            self.cache[k] = v

        self.pending_deltas[hcl] = {
            'writes': deltas,
            'reads': self.pending_reads
        }

        # Clear the top cache
        self.pending_reads = {}
        self.pending_writes.clear()

    def soft_apply_rewards(self, hcl: str):
        deltas = {}

        for k, v in self.pending_writes.items():
            current = self.pending_reads.get(k)
            deltas[k] = (current, v)

            self.cache[k] = v

        self.pending_deltas[hcl]['rewards'] = deltas

        # Clear the top cache
        self.pending_reads = {}
        self.pending_writes.clear()

    def hard_apply(self, hlc):
        # see if the HCL even exists
        if self.pending_deltas.get(hlc) is None:
            return

        # Run through the sorted HCLs from oldest to newest applying each one until the hcl committed is

        to_delete = []
        for _hlc, _deltas in sorted(self.pending_deltas.items()):

            # Run through all state changes, taking the second value, which is the post delta
            for key, delta in _deltas['writes'].items():
                self.driver.set(key, delta[1])
                # self.cache[key] = delta[1]

            # Add the key (
            to_delete.append(_hlc)
            if _hlc == hlc:
                break

        # Remove the deltas from the set
        [self.pending_deltas.pop(key) for key in to_delete]

    # Same as hard apply but for only the most recent changes and the cache
    def commit(self):
        self.cache.update(self.pending_writes)

        for k, v in self.cache.items():
            if v is None:
                self.driver.delete(k)
            else:
                self.driver.set(k, v)

        self.cache.clear()
        self.pending_writes.clear()
        self.pending_reads = {}

    def rollback(self, hlc=None):
        if hlc is None:
            # Returns to disk state which should be whatever it was prior to any write sessions
            self.cache.clear()
            self.pending_reads = {}
            self.pending_writes.clear()
            self.pending_deltas.clear()
        else:
            to_delete = []
            for _hlc, _deltas in sorted(self.pending_deltas.items())[::-1]:
                # Clears the current reads/writes, and the reads/writes that get made when rolling back from the
                # last HLC
                self.pending_reads = {}
                self.pending_writes.clear()


                if _hlc < hlc:
                    # if we are less than the HLC then top processing anymore, this is our rollback point
                    break
                else:
                    # if we are still greater than or equal to then mark this as delete and rollback its changes
                    to_delete.append(_hlc)
                    # Run through all state changes, taking the second value, which is the post delta
                    for key, delta in _deltas['writes'].items():
                        # self.set(key, delta[0])
                        self.cache[key] = delta[0]

            # Remove the deltas from the set
            [self.pending_deltas.pop(key) for key in to_delete]

    def clear_pending_state(self):
        self.rollback()


class ContractDriver(CacheDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.delimiter = '.'
        self.log = logging.getLogger('Driver')

    def items(self, prefix=''):
        # Get all of the items in the cache currently
        _items = {}
        keys = set()

        for k, v in self.pending_writes.items():
            if k.startswith(prefix) and v is not None:
                _items[k] = v
                keys.add(k)

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
        return self.get(key)

    def set_var(self, contract, variable, arguments=[], value=None, mark=True):
        key = self.make_key(contract, variable, arguments)
        self.set(key, value)

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

    def rollback_drivers(self, hlc_timestamp):
        # Roll back the current state to the point of the last block consensus
        self.log.debug(f"Length of Pending Deltas BEFORE {len(self.driver.pending_deltas.keys())}")
        self.log.debug(f"rollback to hlc_timestamp: {hlc_timestamp}")

        if hlc_timestamp is None:
            # Returns to disk state which should be whatever it was prior to any write sessions
            self.cache.clear()
            self.reads = set()
            self.pending_writes.clear()
            self.pending_deltas.clear()
        else:
            to_delete = []
            for _hlc, _deltas in sorted(self.pending_deltas.items())[::-1]:
                # Clears the current reads/writes, and the reads/writes that get made when rolling back from the
                # last HLC
                self.reads = set()
                self.pending_writes.clear()


                if _hlc < hlc_timestamp:
                    self.log.debug(f"{_hlc} is less than {hlc_timestamp}, breaking!")
                    # if we are less than the HLC then top processing anymore, this is our rollback point
                    break
                else:
                    # if we are still greater than or equal to then mark this as delete and rollback its changes
                    to_delete.append(_hlc)
                    # Run through all state changes, taking the second value, which is the post delta
                    for key, delta in _deltas['writes'].items():
                        # self.set(key, delta[0])
                        self.cache[key] = delta[0]

            # Remove the deltas from the set
            self.log.debug(to_delete)
            [self.pending_deltas.pop(key) for key in to_delete]

        #self.driver.rollback(hlc=hlc_timestamp)

        self.log.debug(f"Length of Pending Deltas AFTER {len(self.driver.pending_deltas.keys())}")


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
