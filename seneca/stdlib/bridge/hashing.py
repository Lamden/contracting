import hashlib

'''
Bytes can't be stored in JSON so we use hex-strings converted into bytes and back.
'''


def sha3(hex_str: str):
    byte_str = bytes.fromhex(hex_str)

    hasher = hashlib.sha3_256()
    hasher.update(byte_str)

    hashed_bytes = hasher.digest()

    return hashed_bytes.hex()


def sha256(hex_str: str):
    byte_str = bytes.fromhex(hex_str)

    hasher = hashlib.sha256()
    hasher.update(byte_str)

    hashed_bytes = hasher.digest()

    return hashed_bytes.hex()


exports = {
    'crypto.sha3': sha3,
    'crypto.sha256': sha256
}
