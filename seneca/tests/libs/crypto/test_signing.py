from unittest import TestCase
from seneca.libs.crypto import signing
import nacl


class TestSigning(TestCase):
    def test_signing(self):
        s = nacl.signing.SigningKey.generate()
        msg = b'howdy partner'

        sig = s.sign(msg)

        # pynacl includes the message in the signature, which we are not interested in
        sig = sig[:-len(msg)]

        v = s.verify_key.encode()

        self.assertTrue(signing.verify(v, msg, sig))
