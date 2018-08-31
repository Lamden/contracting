import nacl
import nacl.encoding
import nacl.signing


def verify(v: bytes, msg: bytes, sig: bytes):
    v = nacl.signing.VerifyKey(v)
    try:
        v.verify(msg, sig)
    except nacl.exceptions.BadSignatureError:
        return False
    return True
