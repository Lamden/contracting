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

def run_tests(_):
    import doctest, sys
    #return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})

    from seneca.execute import Empty

    res = Empty()
    res.attempted = 0
    res.failed = 0

    s = nacl.signing.SigningKey.generate()
    msg = b'howdy partner'

    sig = s.sign(msg)

    # pynacl includes the message in the signature, which we are not interested in
    sig = sig[:-len(msg)]

    v = s.verify_key.encode()

    if verify(v, msg, sig):
        res.attempted = 1
    else:
        res.failed = 1

    return res