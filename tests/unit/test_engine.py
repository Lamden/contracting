from unittest import TestCase
import nacl.signing
import json
from contracting.execution.executor import Engine


class TestEngine(TestCase):
    def test_init(self):
        e = Engine()

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