from unittest import TestCase
import nacl.signing
import json
from contracting.execution.executor import Engine
from contracting.db.driver import ContractDriver

driver = ContractDriver()


class TestEngine(TestCase):
    def tearDown(self):
        driver.flush()

    def test_verify_good_tx_structure(self):
        tx = {
            'sender': 'public key in hex',
            'signature': 'hex of payload which is alphabetized json for now...',
            'payload': {
                'contract': 'string',
                'function': 'string',
                'arguments': {
                    'string': 123,
                }
            }
        }

        e = Engine()
        self.assertTrue(e.verify_tx_structure(tx))

    def test_verify_bad_tx_missing_key(self):
        tx = {
            'signature': 'hex of payload which is alphabetized json for now...',
            'payload': {
                'contract': 'string',
                'function': 'string',
                'arguments': {
                    'string': 123,
                }
            }
        }

        e = Engine()
        self.assertFalse(e.verify_tx_structure(tx))

    def test_verify_bad_tx_payload_key(self):
        tx = {
            'sender': 'public key in hex',
            'signature': 'hex of payload which is alphabetized json for now...',
            'payload': {
                'function': 'string',
                'arguments': {
                    'string': 123,
                }
            }
        }

        e = Engine()
        self.assertFalse(e.verify_tx_structure(tx))

    def test_verify_tx_fails_if_expecting_stamps(self):
        tx = {
            'sender': 'public key in hex',
            'signature': 'hex of payload which is alphabetized json for now...',
            'payload': {
                'contract': 'string',
                'function': 'string',
                'arguments': {
                    'string': 123,
                }
            }
        }

        e = Engine(stamps_enabled=True)
        self.assertFalse(e.verify_tx_structure(tx))

    def test_verify_tx_fails_if_expecting_timestamp(self):
        tx = {
            'sender': 'public key in hex',
            'signature': 'hex of payload which is alphabetized json for now...',
            'payload': {
                'contract': 'string',
                'function': 'string',
                'arguments': {
                    'string': 123,
                }
            }
        }

        e = Engine(timestamps_enabled=True)
        self.assertFalse(e.verify_tx_structure(tx))

    def test_verify_tx_signature_succeeds(self):
        nakey = nacl.signing.SigningKey.generate()

        pk = nakey.verify_key.encode().hex()

        tx = {
            'sender': pk,
            'signature': None,
            'payload': {
                'contract': 'string',
                'function': 'string',
                'arguments': {
                    'string': 123,
                }
            }
        }

        message = json.dumps(tx['payload']).encode()

        sig = nakey.sign(message)[:64].hex()

        tx['signature'] = sig

        e = Engine()

        self.assertTrue(e.verify_tx_signature(tx))

    def test_verify_tx_signature_fails(self):
        nakey = nacl.signing.SigningKey.generate()

        pk = nakey.verify_key.encode().hex()

        tx = {
            'sender': pk,
            'signature': None,
            'payload': {
                'contract': 'string',
                'function': 'string',
                'arguments': {
                    'string': 123,
                }
            }
        }

        message = json.dumps(tx['payload']).encode()

        sig = nakey.sign(message)[:64].hex()

        tx['signature'] = sig[:2]

        e = Engine()

        self.assertFalse(e.verify_tx_signature(tx))

    def test_submission_contract_works_on_engine(self):
        driver.flush()

        with open('../../contracting/contracts/submission.s.py') as f:
            contract = f.read()

        driver.set_contract(name='submission',
                            code=contract,
                            author='sys')

        with open('./test_sys_contracts/currency.s.py') as file:
            contract_code = file.read()

        nakey = nacl.signing.SigningKey.generate()

        pk = nakey.verify_key.encode().hex()

        tx = {
            'sender': pk,
            'signature': None,
            'payload': {
                'contract': 'submission',
                'function': 'submit_contract',
                'arguments': {
                    'code': contract_code,
                    'name': 'stu_bucks'
                }
            }
        }

        message = json.dumps(tx['payload']).encode()

        sig = nakey.sign(message)[:64].hex()

        tx['signature'] = sig

        e = Engine()

        output = e.run(tx)

        print(output)