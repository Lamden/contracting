import hashlib
import os
import redis
import base58

#import bnb9whr3dcpguk93myqsj1ii69oscz4jsy7j8dgu1fyfp1hibbw8

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

code_str = open('./example_contracts/_01_currency.seneca', 'r').read()

rr = RedisContractStorage()
contract = Contract.build(code_str=code_str, author='stu', datetime=None, random_seed=None)

r = rr.save(contract)
print(r)
print(rr.load(r))

# def numberToBase(n, b):
#     if n == 0:
#         return [0]
#     digits = []
#     while n:
#         digits.append(int(n % b))
#         n //= b
#     return digits[::-1]

# h = int(hashlib.sha3_256(b'asdfsf').hexdigest(), 16)
# hh = numberToBase(h, 32)
# alpha = 'ybndrfg8ejkmcpqxot1uwisza345h769'

# print(''.join([alpha[i] for i in hh]))

