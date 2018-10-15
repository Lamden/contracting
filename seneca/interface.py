import hashlib
import os
import redis
import base58


# import bnb9whr3dcpguk93myqsj1ii69oscz4jsy7j8dgu1fyfp1hibbw8

class Context:
    pass


class Session:
    def interprete(self, contract_id):
        pass


class ASTParser:
    pass


class ContractStorage:
    def __init__(self):
        raise NotImplementedError

    def save(self, contract):
        raise NotImplementedError

    def load(self, contract_id):
        raise NotImplementedError

    def contract_repr(self, contract):
        raise NotImplementedError


class Contract:
    def build(code_str, author, datetime, random_seed):
        return {
            'code_str': code_str,
            'author': author,
            'submission_time': datetime,
            'random_seed': random_seed
        }


class RedisContractStorage(ContractStorage):
    def __init__(self, driver=redis.StrictRedis(host='localhost',
                                                port=6379,
                                                db=0)):
        self.r = driver

    def save(self, contract):
        contract_id = self.generate_address(contract)

        self.r.hmset(contract_id, {'code_str': contract['code_str'],
                                   'author': contract['author'],
                                   'submission_time': contract['submission_time']})

        return contract_id

    def load(self, contract_id):
        code_str, author, submission_time = \
            self.r.hmget(contract_id, ('code_str', 'author', 'submission_time',))

        runtime_data = {
            'author': author.decode(),
            'now': submission_time.decode(),
            'contract_id': contract_id
        }

        return runtime_data, code_str.decode()

    def generate_address(self, contract):
        h = hashlib.sha3_256()
        h.update(contract['code_str'].encode())
        h.update(contract['author'].encode())

        count = self.r.incr('contract_count:' + contract['author'])

        h.update(str(count).encode())

        encoding = base58.b58encode(h.digest()).decode()

        return encoding