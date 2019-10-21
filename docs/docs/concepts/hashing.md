## hashlib Standard Library

`hashlib` is an extremely small analog to the much more powerful Python hashlib equivalent. They do not share the same API. The Contracting version does not require setting up an object and updating it with bytes. The following functions are available on `hashlib`.

### hashlib.sha3(hex_str: str)

Accepts a valid hexidecimal string and returns a hexidecimal string representation of the SHA3 256 bit hash it produces. If the argument is not a valid hexidecimal string, it will encode the string to bytes and use that for the hash.

### hashlib.sha256(hex_str: str)

Equal functionality to `sha3` but uses the SHA2 256 hash instead. This cryptographic hashing algorithm is used in Bitcoin.