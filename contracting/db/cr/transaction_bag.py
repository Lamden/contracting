from ...logger import get_logger
from typing import Callable
from decimal import Decimal
# import os
# from contracting import capnp as schemas
# import capnp
#
# transaction_capnp = capnp.load(os.path.dirname(schemas.__file__) + '/transaction.capnp')


# class Metadata:
#     def __init__(self, proof, signature, timestamp):
#         self.proof = proof
#         self.signature = signature
#         self.timestamp = timestamp
#
#
# class Payload:
#     def __init__(self, sender, nonce, stamps_supplied, contract_name, function_name, kwargs):
#         self.sender = sender
#         self.nonce = nonce
#         self.stampsSupplied = stamps_supplied
#         self.contractName = contract_name
#         self.functionName = function_name
#         self.kwargs = kwargs
#
#
# class UnpackedContractTransaction:
#     def __init__(self, capnp_struct: transaction_capnp.ContractTransaction):
#         unpacked_tx = capnp_struct.to_dict()
#
#         self.metadata = Metadata(proof=unpacked_tx['metadata']['proof'],
#                                  signature=unpacked_tx['metadata']['signature'],
#                                  timestamp=unpacked_tx['metadata']['timestamp'])
#
#         kwargs = {}
#         for entry in unpacked_tx['payload']['kwargs']['entries']:
#
#             # Unpack the dynamic dictionary in to key and arg
#             k, v = list(entry['value'].items())[0]
#
#             if k == 'fixedPoint':
#                 v = Decimal(v)
#             elif k == 'text':
#                 v = str(v)
#             elif k == 'data':
#                 v = bytes(v)
#             elif k == 'bool':
#                 v = bool(v)
#
#             kwargs[entry['key']] = v
#
#         self.payload = Payload(sender=unpacked_tx['payload']['sender'],
#                                nonce=unpacked_tx['payload']['nonce'],
#                                stamps_supplied=unpacked_tx['payload']['stampsSupplied'],
#                                contract_name=unpacked_tx['payload']['contractName'],
#                                function_name=unpacked_tx['payload']['functionName'],
#                                kwargs=kwargs)

log = get_logger('Contracting[TX-Bag]')

class TransactionBag:
    def __init__(self, transactions: list, input_hash: str, completion_handler: Callable, environment={}):

        self.input_hash = input_hash
        self.transactions = transactions
        self.to_yield = list(range(len(self.transactions)))
        self.completion_handler = completion_handler
        self.environment = environment

    def __iter__(self):
        for i in self.to_yield:
            yield i, self.transactions[i]

    def yield_from(self, idx):
        log.info('Yielding TX')
        """
        Update the list of indicies to yield from a new start point

        :param idx: index to begin the yield from
        :return:
        """
        if idx > 0:
            self.to_yield = list(range(idx, len(self.transactions)))

    def get_tx_at_idx(self, idx):
        return self.transactions[idx]
