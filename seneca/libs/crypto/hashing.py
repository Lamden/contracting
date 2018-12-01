import hashlib
from functools import partial

'''
    Highly abstracted hashing library that exposes the algorithms guaranteed by hashlib a la Python 3.
    These functions are the following: blake2b, sha3_384, sha3_224, md5, sha256, sha512, sha1, sha224, 
    sha3_256, sha3_512, sha384

    Shake functions aren't available because they are obscure and add complexity to hashing which should be as easy
    as possible to tooling with.
'''

supported_hashing_functions = hashlib.algorithms_guaranteed
supported_hashing_functions.remove('shake_128')
supported_hashing_functions.remove('shake_256')
supported_hashing_functions.remove('blake2s')


def hash_data(d: bytes, algo: str, as_hex=False):
    assert algo in supported_hashing_functions
    assert type(d) == bytes, 'd must be of type bytes.'

    m = hashlib.new(algo)
    m.update(d)
    return m.hexdigest() if as_hex else m.digest()


def f(algo: str):
    assert algo in supported_hashing_functions

    return partial(hash_data, algo=algo)


exports = {
    key: f(key) for key in supported_hashing_functions
}
