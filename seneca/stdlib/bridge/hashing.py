import hashlib


def sha3(b: bytes):
    s = hashlib.sha3_256()
    s.update(b)
    return s.digest()


exports = {
    'hashing.sha3': sha3
}
